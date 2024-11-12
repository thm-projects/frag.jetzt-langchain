import os
import re
import hashlib


def load_file(name: str):
    with open(
        f"{os.getcwd()}/app/ai_conversation/db_statements/{name}.sql", "r"
    ) as file:
        return file.read()


def _get_files():
    list_of_files = os.listdir(f"{os.getcwd()}/app/ai_conversation/db_files")
    # filter out files that do not start with a number
    p = re.compile("^\d+_.*\.sql$")
    new_list = []
    for file in filter(p.match, list_of_files):
        splitted = file.split("_", 1)
        number = int(splitted[0])
        name, format = splitted[1].rsplit(".", 1)
        if format not in ["sql", "sh"]:
            exit(f"Migration {file} has an invalid format")
        new_list.append([number, name, file, format])
    new_list.sort(key=lambda x: x[0])
    return new_list


async def migrate(async_connection_pool):
    list_of_files = _get_files()
    ensure_migration = load_file("ensure_migration")

    async with async_connection_pool.acquire() as conn:
        await conn.execute(ensure_migration)
        for file in list_of_files:
            content = ""
            with open(
                f"{os.getcwd()}/app/ai_conversation/db_files/{file[2]}", "r"
            ) as f:
                content = f.read()
            hash = hashlib.sha256(content.encode()).hexdigest()
            saved_hash = await conn.fetchval(
                "SELECT hash FROM migration WHERE version = $1;", file[0]
            )
            if saved_hash is not None:
                if hash != saved_hash:
                    exit(f"Migration {file[0]}: {file[1]} has been modified")
                else:
                    continue
            print(f"Running migration {file[0]}: {file[1]}", flush=True)
            try:
                if file[3] == "sql":
                    await conn.execute(content)
                else:
                    result = os.system(f"bash {os.getcwd()}/app/ai_conversation/db_files/{file[2]}")
                    if result != 0:
                        exit(f"Migration {file[0]}: {file[1]} failed")
                await conn.execute(
                    "INSERT INTO migration(version, hash) VALUES ($1, $2);",
                    file[0],
                    hash,
                )
            except Exception as e:
                print(f"Migration failed: {e}", flush=True)
                exit("Migration failed")
                break

        print("Migration up to date")
