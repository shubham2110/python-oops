
import pathlib
import threading
from SingletonMeta import SingletonMeta
from functools import _make_key
import os
import pathlib
import json
import queue
import asyncio
import queue
import pickle
from datetime import datetime

class FunCache(metaclass=SingletonMeta):

    cache={}

    def __init__(self, cachedir='Cache/', sync_from_disk_time=30, sync_to_disk_time=30):
        """
            It will cache all the key value pair in 'cachefilepath'. It will sync_from_disk every 30 min and sync_to_disk every 30 min. 
        """
        self.cache_write_lock=queue.Queue(1)   #TODO:  it would have better if I make a lock file. 
        self.locks={}
        basedir = os.path.abspath(os.path.dirname(__file__))
        cachedirpath=os.path.join(basedir,cachedir)
        self.cachedir=pathlib.Path(cachedirpath)
        if not self.cachedir.is_dir():
            os.mkdir(self.cachedir)
            print("Creating Cache folder at: ", self.cachedir)
        
    def key_to_filename(self, key):
        import hashlib
        return hashlib.sha256(key.encode('utf-8')).hexdigest()
    

    def get(self,key):
        value=self.cache.get(key, None)
        if value:
            return value
        else:
            if not pathlib.Path(os.path.join(self.cachedir,self.key_to_filename(key))).is_file():
                return None
            with open(os.path.join(self.cachedir,self.key_to_filename(key)), "rb") as f:
                d=pickle.load(f)
                self.cache.update(d)
                return d.get(key,None)

    def put(self,key, value):
        self.cache[key]=value

        if not self.locks.get(key, None):
            self.locks[key]=queue.Queue(1)
        
        # Stupid way
        self.locks[key].put(1)
        with open(os.path.join(self.cachedir,self.key_to_filename(key)), "wb") as f:
            pickle.dump({key: value}, f)
        self.locks[key].get()

    def remove_dynamic_objects_from_key(self, key):
        import re
        for x in re.findall(r', <.*0x.*>,',key): 
            key=key.replace(x,",")
        return key

    def cached(self,func):
        def cache2(*args, **kwargs):
                key_kwargs = {k: v for k, v in kwargs.items()}
                key=str(_make_key(
                (func.__module__, func.__qualname__,) + args, key_kwargs,
                typed=False, kwd_mark=("_KWD_MARK_",)))
                
                key=self.remove_dynamic_objects_from_key(key)

                if not self.get(key):
                    value=func(*args, **kwargs)
                    self.put(key, value)
                    print("Miss:", key)
                else:
                    #print("Hit: ", key )
                    pass
                return self.cache[key]
        return cache2
    
