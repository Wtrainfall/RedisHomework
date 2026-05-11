import os

REDIS_CONFIG = {
    'host': os.getenv('REDIS_HOST', 'localhost'),
    'port': int(os.getenv('REDIS_PORT', 6379)),
    'db': 0,
    'decode_responses': True,
}

DB_PATH = os.getenv('DB_PATH', 'data/social.db')

BF_KEY = 'bf:users'
BF_ERROR_RATE = 0.01
BF_INITIAL_SIZE = 1000

CF_KEY_PREFIX = 'cf:likes:post'  
CF_CAPACITY = 10000             
CF_BUCKET_SIZE = 4            
CF_MAX_ITERATIONS = 20          
CF_EXPANSION = 1                 