from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from enum import StrEnum
from typing import Optional, Tuple
from uuid import UUID
from app.ai_conversation.db_decorator import entity
from app.ai_conversation.services.role_checker import Role
import pytz


class RestrictionTarget(StrEnum):
    ALL = "ALL"
    UNREGISTERED = "UNREGISTERED"
    REGISTERED = "REGISTERED"
    USER = "USER"
    UNREGISTERED_USER = "UNREGISTERED_USER"
    REGISTERED_USER = "REGISTERED_USER"
    MOD = "MOD"
    UNREGISTERED_MOD = "UNREGISTERED_MOD"
    REGISTERED_MOD = "REGISTERED_MOD"
    CREATOR = "CREATOR"


def applies_for_restriction(config: dict, target: RestrictionTarget) -> bool:
    if target == RestrictionTarget.ALL:
        return True
    role = config["configurable"]["role"]
    is_registered = config["configurable"]["user_info"]["type"] == "registered"
    if target == RestrictionTarget.UNREGISTERED:
        return not is_registered
    if target == RestrictionTarget.REGISTERED:
        return is_registered
    if target == RestrictionTarget.USER:
        return role == Role.PARTICIPANT
    if target == RestrictionTarget.UNREGISTERED_USER:
        return role == Role.PARTICIPANT and not is_registered
    if target == RestrictionTarget.REGISTERED_USER:
        return role == Role.PARTICIPANT and is_registered
    if target == RestrictionTarget.MOD:
        return role == Role.MODERATOR
    if target == RestrictionTarget.UNREGISTERED_MOD:
        return role == Role.MODERATOR and not is_registered
    if target == RestrictionTarget.REGISTERED_MOD:
        return role == Role.MODERATOR and is_registered
    if target == RestrictionTarget.CREATOR:
        return role == Role.CREATOR
    return False


def find_next_boundaries(
    times: list[datetime], timezone: str, strategy: str
) -> list[Tuple[datetime, datetime]]:
    try:
        num, group = strategy[:-1], strategy[-1:]
        num = int(num)
        tz = pytz.timezone(timezone)
        target = pytz.timezone("UTC")
        time = times[0]
        adjusted_time = tz.normalize(time)
        current_time = tz.normalize(datetime.now())
        if group == "y":
            diff = current_time.year - adjusted_time.year
            if current_time < adjusted_time.replace(year=current_time.year):
                diff -= 1
            # diff is always positive
            diff = diff // num
            result = []
            for time in times:
                start = tz.normalize(time)
                start = start.replace(year=start.year + num * diff)
                end = tz.normalize(time)
                end = end.replace(year=start.year + num)
                result.append((target.normalize(start), target.normalize(end)))
            return result

        if group == "M":
            diff = (current_time.year - adjusted_time.year) * 12 - (
                current_time.month - adjusted_time.month
            )
            if current_time < adjusted_time.replace(
                year=current_time.year, month=current_time.month
            ):
                diff -= 1
            # diff is always positive
            diff = diff // num
            result = []
            for time in times:
                start = tz.normalize(time)
                month_diff = num * diff + start.year * 12
                year_diff = month_diff // 12
                month_diff = month_diff % 12
                start = start.replace(year=year_diff, month=month_diff + 1)
                month_diff = month_diff + num
                year_diff = year_diff + month_diff // 12
                month_diff = month_diff % 12
                end = start.replace(year=year_diff, month=month_diff + 1)
                result.append((target.normalize(start), target.normalize(end)))
            return result

        if group == "d" or group == "w":
            num = num * 7 if group == "w" else num
            delta = current_time - adjusted_time
            days = delta.day + round(delta.seconds / 86400)  # fix when dst occur
            diff = days // num
            day_diff = diff * num
            result = []
            for time in times:
                start = tz.localize(time + timedelta(days=day_diff))
                end = tz.localize(time + timedelta(days=day_diff + num))
                result.append((target.normalize(start), target.normalize(end)))
            return result
    except (ValueError, pytz.UnknownTimeZoneError):
        return None
    return None


@dataclass
class InputRestrictions:
    account_id: Optional[UUID]
    room_id: Optional[UUID]


@entity
@dataclass
class Restrictions:
    id: UUID
    account_id: UUID
    room_id: UUID
    created_at: datetime
    updated_at: datetime


@dataclass
class InputBlockRestriction:
    restriction_id: UUID
    target: RestrictionTarget


@entity
@dataclass
class BlockRestriction:
    id: UUID
    restriction_id: UUID
    target: RestrictionTarget
    created_at: datetime
    updated_at: datetime

    def is_user_allowed(self, config: dict) -> bool:
        return not applies_for_restriction(config, self.target)


@dataclass
class QuotaReservation:
    id: UUID
    time: datetime
    reserved: Decimal


NULL_RESERVATION = QuotaReservation(None, None, Decimal(0))


@dataclass
class InputQuotaRestriction:
    restriction_id: UUID
    quota: Decimal
    target: RestrictionTarget
    reset_strategy: str
    timezone: str
    last_reset: datetime
    end_time: Optional[datetime]


@entity
@dataclass
class QuotaRestriction:
    id: UUID
    restriction_id: UUID
    quota: Decimal
    counter: Decimal
    target: RestrictionTarget
    reset_strategy: str
    # Reset strategy can be one of the following:
    # - "daily": 5d
    # - "monthly": 5M
    # - "yearly": 5y
    # - "weekly": 5w
    timezone: str
    last_reset: datetime
    # Fixed reset time, if reset_strategy contains a fixed unit
    end_time: datetime
    created_at: datetime
    updated_at: datetime

    def is_user_allowed(self, config: dict) -> dict:
        has_ended = self.end_time and self.end_time <= datetime.now()
        has_started = self.last_reset <= datetime.now()
        allowed = applies_for_restriction(config, self.target)
        result = find_next_boundaries(
            [self.last_reset], self.timezone, self.reset_strategy
        )
        has_reset = result and result[0][0] > self.last_reset
        return {
            "has_ended": not has_ended,
            "has_started": has_started,
            "role": {"needed": self.target, "allowed": allowed},
            "quota_is_null": self.quota <= 0,
            "quota_available": self.quota if has_reset else self.quota - self.counter,
        }

    def reserve_quota(
        self, config: dict, min_amount: Decimal, max_amount: Decimal
    ) -> Optional[QuotaReservation]:
        if self.end_time and self.end_time <= datetime.now():
            return None
        if self.last_reset > datetime.now():
            return None
        if not applies_for_restriction(config, self.target):
            return None
        if self.quota <= 0:
            return NULL_RESERVATION
        result = find_next_boundaries(
            [self.last_reset], self.timezone, self.reset_strategy
        )
        if result and result[0][0] > self.last_reset:
            self.last_reset = result[0]
            self.counter = 0
        if self.counter + min_amount > self.quota:
            return NULL_RESERVATION
        rest_quota = self.quota - (self.counter + min_amount)
        using = min(rest_quota, max_amount - min_amount) + min_amount
        if using < 1:  # When using = 0, min_amount = 0
            return NULL_RESERVATION
        self.counter = self.counter + using
        return QuotaReservation(self.id, self.last_reset, using)

    def free_unused_quota(self, reservation: QuotaReservation, used: Decimal) -> bool:
        if reservation.id != self.id:
            return False
        if reservation.time != self.last_reset:
            # Not in same time scope anymore
            return True
        self.counter = self.counter + used - reservation.reserved
        return True


@dataclass
class InputTimeRestriction:
    restriction_id: UUID
    start_time: datetime
    end_time: datetime
    target: RestrictionTarget
    repeat_strategy: str
    timezone: str


@entity
@dataclass
class TimeRestriction:
    id: UUID
    restriction_id: UUID
    start_time: datetime
    end_time: datetime
    target: RestrictionTarget
    repeat_strategy: str
    timezone: str
    created_at: datetime
    updated_at: datetime

    def is_user_allowed(self, config: dict) -> dict:
        dt = datetime.now()
        not_started = True if self.start_time > dt else False
        allowed = applies_for_restriction(config, self.target)
        boundaries = find_next_boundaries(
            [self.start_time, self.end_time], self.timezone, self.repeat_strategy
        )
        is_in_time = False
        if not boundaries:
            is_in_time = self.start_time <= dt and self.end_time >= dt
        else:
            is_in_time = boundaries[0][0] <= dt and boundaries[1][0] >= dt
        return {
            "not_started": not_started,
            "role": {"needed": self.target, "allowed": allowed},
            "is_in_time": is_in_time,
        }
