import re

import coc
import asyncio
import orjson
import os
import pathlib
from typing import Dict, Any
import aiohttp

async def get_json_files() -> list[pathlib.Path]:
    mockdata_dir = pathlib.Path(__file__).parent
    files = []
    for file in mockdata_dir.rglob("*.json"):
        files.append(file.relative_to(mockdata_dir))
    return files


async def parse_json_file(file_path: pathlib.Path) -> Dict[str, Any]:
    with open(file_path, "rb") as f:
        return orjson.loads(f.read())



async def regenerate_json(file_path: pathlib.Path, new_data: Dict[str, Any]):
    with open(file_path, "wb") as f:
        f.write(orjson.dumps(new_data, option=orjson.OPT_INDENT_2))


async def main():
    coc_client = coc.Client(raw_attribute=True, lookup_cache=False, update_cache=False)
    try:
        await coc_client.login(os.environ.get("DEV_SITE_EMAIL"),
                               os.environ.get("DEV_SITE_PASSWORD"))
    except coc.InvalidCredentials as error:
        exit(error)
    
    json_files = await get_json_files()
    headers = {
        "Accept": "application/json",
        "authorization": "Bearer {}".format(next(coc_client.http.keys)),
        "Accept-Encoding": "gzip, deflate",
    }
    async with aiohttp.ClientSession(headers=headers) as session:
        for file_path in json_files:
            original_data = await parse_json_file(file_path)
            original_response_code = original_data.get("response_code")
            if not original_data:
                continue
            if not original_data.get("endpoint"):
                continue
            endpoint = original_data["endpoint"]
            if re.findall(r"{{[A-Za-z_]*}}", endpoint) and not original_data.get("args"):
                continue
            endpoint = endpoint.format(**original_data.get("args", {})).replace('#', '%23')
            # get a token from the coc_client
            async with session.get(coc_client.http.base_url + endpoint) as resp:
                if resp.status != original_response_code:
                    print(f"Error fetching data for {endpoint}: {resp.status}")
                    continue
                # get the body
                try:
                    body = await resp.json()
                except Exception:
                    body = await resp.text()
                # get the response headers
                response_headers = resp.headers
                
                # update the original data with the new data
                org_headers = original_data.get('headers', {})
                if response_headers.get('cache-control'):
                    org_headers['cache-control'] = response_headers.get('cache-control')
                if response_headers.get('content-type'):
                    org_headers['content-type'] = response_headers.get('content-type')
                original_data['headers'] = org_headers
                original_data['body'] = body
                await regenerate_json(file_path, original_data)
            



if __name__ == '__main__':
    asyncio.run(main())
