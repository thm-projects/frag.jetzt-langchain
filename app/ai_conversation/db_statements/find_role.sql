SELECT 
    CASE 
        WHEN r.owner_id = $1 THEN 'CREATOR' 
        WHEN ra.role IS NULL THEN 'NULL'
        ELSE ra.role 
    END AS "role" 
FROM 
    room r 
LEFT JOIN 
    room_access ra 
    ON r.id = ra.room_id 
    AND ra.account_id = $1 
WHERE 
    r.id = $2;