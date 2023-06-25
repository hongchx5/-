import random
from util import instance as inst
from util import policy as pol
import numpy as np


class Simulator:
    def __init__(self):  ##创建一个库存模拟器实例
        # Instance type to simulate
        self.instance = inst.InventoryInstance()
        # Policy we want to simulate
        self.policy = pol.InventoryPolicy()
        # number of simulations to run
        self.nr_simulations = 1

    def simulate(self, k):  ##用于模拟给定库存策略下的总成本。函数接受一个随机种子作为参数
        temp = 0.0   ##temp来表示总成本
        random.seed(k)
        i = self.instance.init_inv  ##当前库存水平i
        for t in range(self.instance.n):
            if self.policy.R[t] == 1:   ##根据当前策略中的R向量判断当前时间是否需要进行库存审查
                temp += self.instance.cr   ##固定的审查成本
                if i <= self.policy.s[t]:  ##判断库存水平i是否低于策略中的s[t]
                    temp += self.instance.co + self.instance.cl * (self.policy.S[t] - i)  ##计算订单成本
                    i = self.policy.S[t]
            i -= self.instance.gen_demand(t)  ##减去当前需求量
            temp += (self.instance.ch * i if i > 0 else - self.instance.cp * i)  ##持有成本或缺货成本
        return temp

    def multiple_simulations(self, nr, seed):  ##函数用于进行多次模拟，计算给定库存策略下的平均总成本。函数接收两个参数：模拟次数nr和随机种子seed
        np.random.seed(seed)  ##设定随机数发生器的初始状态
        seed_list = np.random.randint(0, 10000, nr)##一个长度为nr的随机整数数组seed_list
        avg = 0
        for i in seed_list:
            i=int(i)
            avg += self.simulate(i)
        return avg/nr   ##计算nr次的平均成本

    memo = {}
    def get_cost(self, t, i):  ##在给定时间 t 和给定库存水平 i 下的总成本期望
        if t == self.instance.n:
            return 0
        if (t,i) in self.memo:
            return self.memo[(t,i)]

        if self.policy.R[t] == 0:
            temp = 0
            for d in range(len(self.instance.prob[t])):  #d是需求，prob是d的密度函数
                if self.instance.prob[t][d] == 0:
                    continue
                temp += self.instance.prob[t][d] * self.get_cost(t+1, i-d) ##求期望
                if i >= d:
                    temp += self.instance.prob[t][d] * self.instance.ch * (i-d)
                else:
                    temp += self.instance.prob[t][d] * self.instance.cp * (d-i)  
        elif i <= self.policy.s[t]:
            temp = self.instance.cr + self.instance.co
            for d in range(len(self.instance.prob[t])):
                if self.instance.prob[t][d] == 0:
                    continue
                temp += self.instance.prob[t][d] * self.get_cost(t+1, self.policy.S[t]-d)
                if self.policy.S[t] >= d:
                    temp += self.instance.prob[t][d] * self.instance.ch * (self.policy.S[t]-d)
                else:
                    temp += self.instance.prob[t][d] * self.instance.cp * (d-self.policy.S[t])
        else:
            temp = self.instance.cr
            for d in range(len(self.instance.prob[t])):
                if self.instance.prob[t][d] == 0:
                    continue
                temp += self.instance.prob[t][d] * self.get_cost(t+1, i-d)
                if i >= d:
                    temp += self.instance.prob[t][d] * self.instance.ch * (i-d)
                else:
                    temp += self.instance.prob[t][d] * self.instance.cp * (d-i)

        self.memo[(t,i)] = temp
        return temp

    def calc_expected_cost(self): ##计算初始条件下的总成本
        self.memo = {}
        return self.get_cost(0, self.instance.init_inv)
