from multiprocessing import Pool
def clear(i):
    __= 0
    for _ in range(int(1e8*i)):
        __= __ + 1
if __name__ == '__main__':
    pool  = Pool(5)
        
        # 提交任务
    for i in range(50):
        pool.apply_async(func=clear, args=(i+1,))
        
    pool.close()
    pool.join()
    