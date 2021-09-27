
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
from datetime import datetime

class MyCache(metaclass=SingletonMeta):

    cache={}

    def __init__(self, cachefilepath='./local.db', sync_from_disk_time=30, sync_to_disk_time=30):
        """
            It will cache all the key value pair in 'cachefilepath'. It will sync_from_disk every 30 min and sync_to_disk every 30 min. 
        """
      
        self.cache_write_lock=queue.Queue(1)   #TODO:  it would have better if I make a lock file. 
        self.cachefile=pathlib.Path(cachefilepath)
 
        if self.cachefile.is_file():
            # Sync cache from this file
            with open(self.cachefile, 'r') as openfile:
                json_object = json.load(openfile)
                self.cache.update(json_object)
                #print("Initial Cache:", self.cache)
        else:
            pass
        self.schedule_sync_from_disk_async(sync_from_disk_time)


    def schedule_sync_from_disk_async(self, time_in_min):        
        t=threading.Thread(target=self.schedule_sync_from_disk, args=(time_in_min))
        t.start()
    

    def schedule_sync_from_disk(self, time_in_min):        
        t_old=datetime.now()
        while(True):
            t_new=datetime.now()
            if ( (t_new - t_old).total_seconds()/60 > time_in_min ) :
                t_old=t_new
                self.pull_cache_from_disk_async()

    def get(self,key):
        return self.cache[key]

    def put(self,key, value):
        self.cache[key]=value


    def push_cache_to_disk(self):  #TODO: Time based cache invalidation to be added. 
        """
        Saving self.cache to disk for reuse.  
        """
        asyncio.run(asyncio.sleep(6)) # Making it sleep for 3 seconds, for no reason, Actually there is one reason but I need to research on it.  :p
        self.cache_write_lock.put(1) # Locking file to handle race condition. 
        
        cache_before_push={} 

        if self.cachefile.is_file(): # Cache File exists, Before writing, we need to update our local cache with dir cache
            try:
                with open(self.cachefile,'r') as openfile:
                    js=json.load(openfile)
                    js.update(self.cache)
                    cache_before_push.update(js)
            except:
                cache_before_push.update(self.cache)
            
            with open(self.cachefile, 'w') as f:
                json.dump(cache_before_push, f)
        else: # Cache file is not present, hence we can just create a new cache
            cache_before_push.update(self.cache)
        
        with open(self.cachefile, 'w') as f:
            self.cache.update(cache_before_push)
            json.dump(cache_before_push, f)
        
        _=self.cache_write_lock.get()


    def pull_cache_from_disk(self): # TODO: Read from cache only if disk-cache is updated. 
        try:
            with open(self.cachefile,'r') as openfile:
                    js=json.load(openfile)
                    if js['last_updated'] >= self.cache['last_updated']:
                        self.cache.update(js)
                    else:
                        js.update(self.cache)
                        self.cache.update(js)                    
        except:
            pass
            # DO nothing and reply on our cache. 


    def push_cache_to_disk_async(self):
        from threading import Thread
        t1=Thread(target=self.pull_cache_from_disk)
        t1.start()


    def pull_cache_from_disk_async(self):
        from threading import Thread
        t1=Thread(target=self.pull_cache_from_disk)
        t1.start()
        # joining this thread(t1.join()) is ignored because we need to get things updated in background

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

                if not self.cache.get(key, None):
                    value=func(*args, **kwargs)
                    self.put(key, value)
                    self.push_cache_to_disk_async() # Will updte to disk whenever it will get time
                    #print("Miss: ","key:",key)
                else:
                    #print("Hit: ", key )
                    pass
                return self.cache[key]
        return cache2
    
