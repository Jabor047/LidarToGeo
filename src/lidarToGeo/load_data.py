import json
import boto3
import asyncio
from aiohttp import ClientSession
from src.lidarToGeo.ept_info import Info
from src.lidarToGeo.logger import setup_logger

logger = setup_logger("load_data")

s3 = boto3.client("s3")
bucket = "usgs-lidar-public"
bucket_url = "https://s3-us-west-2.amazonaws.com/usgs-lidar-public/"

def list_folders(s3_client: boto3.client, bucket_name: str):
    """
    This function takes an s3 boto3 client and the a s3 bucket's name and
    yields all the folder names in the s3 bucket
    Parameters
    ----------
    s3_client: boto3.client : s3 boto3 client

    bucket_name: str : the desired bucket's name

    Returns : a python generator
    -------

    """
    logger.info(f"fetching folders in {bucket_name}")
    paginator = s3_client.get_paginator('list_objects_v2')
    response_iterator = paginator.paginate(Bucket=bucket_name, Delimiter='/',
                                           Prefix='')

    for page in response_iterator:
        for content in page.get("CommonPrefixes", []):
            yield content.get('Prefix')

async def fetch(region, url, session) -> tuple:
    async with session.get(url) as response:
        return (region, await response.read())

async def run() -> list:
    regions = list_folders(s3, bucket)
    region_info = []
    async with ClientSession() as session:
        logger.info(f"loading the ept.json files from {bucket}")
        for region in regions:
            if region == "USGS_LPC_WA_Western_North_2016_LAS_2018/" or \
                    region == "USGS_LPC_WA_Western_South_2016_LAS_2018/":
                ept_json_path = bucket_url + region + "ept-1.json"
            else:
                ept_json_path = bucket_url + region + "ept.json"
            ept_region_info = asyncio.ensure_future(fetch(region, ept_json_path, session))
            region_info.append(ept_region_info)

        response = await asyncio.gather(*region_info)

    return region_info

def load_ept_json() -> dict:
    """
    calls the asynchronous functions that get all the ept.json files in the usgs-lidar-public bucket
    and passes the result into the Info class so that we can get the data readily


    Returns : a dictionary
    """
    loop = asyncio.get_event_loop()
    future = asyncio.ensure_future(run())
    regions = loop.run_until_complete(future)

    region_ept_info = {}

    for i in range(len(regions)):
        try:
            region_ept_info[regions[i].result()[0]] = Info(regions[i].result()[1].decode())
        except json.decoder.JSONDecodeError as e:
            print(regions[i].result()[0])

    return(region_ept_info)
