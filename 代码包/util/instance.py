import numpy as np
from scipy.stats import poisson
from scipy.stats import norm
import random
import math


class InventoryInstance:
    def __init__(self):
        # Number of periods in the time horizon  最大时期数
        self.n = 1
        # Costs
        # Holding cost per unit per period 滞销惩罚
        self.ch = 0
        # Penalty cost per unit per period  缺货惩罚
        self.cp = 0
        # Linear production/ordering cost per unit 线性的订购成本
        self.cl = 0
        # Fixed ordering cost  固定的订购成本
        self.co = 0
        # Fixed review cost 固定的审查成本
        self.cr = 0

        # Service level 服务水平
        self.alpha = 0

        # Initial inventory 初始库存
        self.init_inv = 0
        # Maximum value of the demand with non null probability  我认为是单个时期最多累积的需求量
        self.max_demand = 60
        # Demand probability distribution 需求的密度函数（离散形式）
        self.prob = []
        # Maxtrix containing the convolutions of the demand probability distribution 需求概率分布卷积
        self.conv_prob = []
        # Average values of the demand distribution  需求分布的均值
        self.means = []
        # Coefficient of variation in case of a normal distributed deman  分布系数
        self.cv = 1 / 3.0
        # Type of demand distribution - poisson or normal 需求分布型
        self.dem_type = "poisson"

        # Maximum and minimum inventory level  最大库存量和最小库存量，设置为需求的n倍
        self.max_inv_level = self.n * self.max_demand
        self.min_inv_level = -self.n * self.max_demand
        # Review times, if fixed  想要固定的审查时间
        self.rev_time = []

    def max_inv_bouding(self, threshold):   # 设定库存量上下界，取需求的某个区间 可以是负数 并且确定了需求的分布
        demand = [0 for _ in range(self.n * self.max_demand + 1)]  # n个时期，最多可以累积n * max_demand的需求
        for i in range(self.max_demand + 1):
            demand[i] = self.prob[0][i]
        for i in range(1, self.n):
            temp = [0 for _ in range(self.n * self.max_demand + 1)]
            for a in range((self.n - 1) * self.max_demand + 1):
                for b in range(self.max_demand + 1):
                    temp[a + b] += self.prob[i][b] * demand[a]  # 求出需求为a+b的概率
            demand = temp
        j = self.n * self.max_demand
        pdf_dem = demand[j]
        while pdf_dem < threshold:  # 从后往前 将发生概率比较小的需求视为不可能事件
            j -= 1
            pdf_dem += demand[j - 1]

        self.max_inv_level = j # 将库存的最大最小值设为可能发生的需求量
        self.min_inv_level = -j//10 + self.init_inv

    def probability_convolution(self):  # 需求卷积分布函数
        self.conv_prob = np.zeros((self.n, self.n, self.n * self.max_demand + 1))  # 创造三维数组

        for i in range(self.n):
            for j in range(self.max_demand+1):
                self.conv_prob[i][i][j] = self.prob[i][j]
            # self.conv_prob[i][i] = self.conv_prob[i][i] / sum(self.conv_prob[i][i])

        for i in range(0, self.n):
            for i2 in range(i+1, self.n):
                for j in range((i2-i)*self.max_demand +1):
                    for j2 in range(self.max_demand+1):
                        self.conv_prob[i][i2][j+j2] += self.conv_prob[i][i2-1][j] * self.prob[i2][j2]
                self.conv_prob[i][i2] = self.conv_prob[i][i2] / sum(self.conv_prob[i][i2])



    # Probability distribution generators based on the means 基于均值的概率分布生成器（意思是下面这几个包括了不一样的分布类型的需求）
    def gen_poisson_probability(self, mu):  # 泊松分布的概率分布
        self.prob = [[0.0 for _ in range(0, self.max_demand +1)] for _ in range(self.n)] # n行max_demand+1列
        for i in range(self.n):
            for j in range(0, self.max_demand +1):
                self.prob[i][j] = poisson.pmf(j, mu)  # 需求为j的概率（泊松分布） 赋值到prob里

    def gen_fix_probability(self, avg):  #  均值分布的概率分布
        self.prob = [[0.0 for _ in range(0, self.max_demand +1)] for _ in range(self.n)]
        if not (2 <= avg <= self.max_demand - 2):
            print("average outside interval allowed")
            return
        for i in range(self.n):
            self.prob[i][avg-2] = 0.1
            self.prob[i][avg-1] = 0.2
            self.prob[i][avg] = 0.4
            self.prob[i][avg+1] = 0.2
            self.prob[i][avg+2] = 0.1

    def gen_bin_probability(self):  # 是对二元分布类型需求的概率分布
        if self.max_demand != 1:
            print("Error - In binary demand max demand has to be equal to 1")
        self.prob = [[0.5, 0.5]for _ in range(self.n)]

    def gen_non_stationary_normal_demand(self, threshold):  # 多个均值的正态分布需求类型的概率分布
        self.dem_type = "normal"
        if len(self.means) != self.n:
            print("wrong size self.means vector")
            return
        self.max_demand = int(norm(loc = max(self.means), scale = self.cv*max(self.means)).ppf(1-threshold))  # 这个函数好像是求正态分布的累积分布函数的逆函数的
        self.prob = [[0.0 for _ in range(0, self.max_demand +1)] for _ in range(self.n)]
        for i in range(self.n):
            norm_dist = norm(loc=self.means[i], scale = self.cv*self.means[i])
            for j in range(self.max_demand +1):
                self.prob[i][j] = norm_dist.pdf(j)  # x=j的概率密度
            self.prob[i] = self.prob[i]/sum(self.prob[i])  #扩充为概率和为1
        self.max_inv_level = self.n * self.max_demand
        self.min_inv_level = - self.n * self.max_demand + self.init_inv

    def gen_non_stationary_poisson_demand(self, sigma,threshold): ## fix this VISE   多个均值的泊松分布的概率分布
        if len(self.means) != self.n:
            print("wrong size self.means vector")
            return
        meanstemp=[0 for _ in range(self.n)]
        for i in range(self.n):
            temp= np.random.normal(self.means[i], sigma, 1)
            temp=temp.tolist()
            meanstemp[i]=temp[0]
        self.means=meanstemp
        print(self.means)
        self.max_demand = int(poisson.ppf(loc = 0 , mu = max(self.means), q = (1-threshold)))
        self.prob = [[0.0 for _ in range(0, self.max_demand +1)] for _ in range(self.n)]
        for i in range(self.n):
            for j in range(self.max_demand +1):
                if self.means[i] != 0 :
                    self.prob[i][j] = poisson.pmf(k = j, mu = self.means[i])
                else:
                    self.prob[i][j] = poisson.pmf(k = j, mu = 0.1)  # 这些都和上面的过程很像
            self.prob[i] = self.prob[i]/sum(self.prob[i])
        #self.max_inv_level = self.n * self.max_demand
        #self.min_inv_level = - self.n * self.max_demand + self.init_inv

    # Pattern generator, they are generlly found in literature  模式生成器 means数组的生成过程
    def gen_means(self, type):
        self.means = [0 for _ in range(self.n)]
        if type == "LCYA":
            for i in range(self.n):
                self.means[i] = round(19 * math.exp(-(i-12)**2) / 5)
        elif type == "SIN1":
            for i in range(self.n):
                self.means[i] = round(70 * math.sin(0.8*(i+1)) +80)
        # Form Rossi et al. 2011
        elif type == "P1": # Form Rossi et al. 2011
            for i in range(self.n):
                self.means[i] = round(50 * (1 + math.sin(math.pi * i /6)))
        elif type == "P2": # Form Rossi et al. 2011
            for i in range(self.n):
                self.means[i] = round(50 * (1 + math.sin(math.pi * i /6))) + i
        elif type == "P3": # Form Rossi et al. 2011
            for i in range(self.n):
                self.means[i] = round(50*(1 + math.sin(math.pi * i /6))) + self.n - i
        elif type == "P4": # Form Rossi et al. 2011
            for i in range(self.n):
                self.means[i] = round(50 * (1 + math.sin(math.pi * i /6))) + min(i, self.n-i)
        elif type == "P5": # Form Rossi et al. 2011
            for i in range(self.n):
                self.means[i] = random.randint(0,100)
            # NEW PATTERNS FOR THE PAPER
        elif type == "STA":  # new patterns for the paper
            for i in range(self.n):
                self.means[i] = 50
        elif type == "INC":
            for i in range(self.n):
                self.means[i] = round((2 * i + 1) * 100 / (2 * self.n))
        elif type == "DEC":
            for i in range(self.n):
                self.means[i] = round(100 - (2 * i + 1) * 100 / (2 * self.n))
        elif type == "LCY1": #the lifecycles can be simplified
            c = 0
            for i in range(int(self.n / 3)):
                self.means[i] = round((2 * i + 1) * 75 / (2 * int(self.n/3)))
            for i in range(int(self.n / 3), 2 * int(self.n / 3) + self.n % 3):
                self.means[i] = 75
            for i in range(2 * int(self.n / 3) + self.n % 3, self.n):
                self.means[i] = round(75 - (2 * c + 1) * 75 / (2 * int(self.n/3 + 0.5)))
                c += 1
        elif type == "LCY2":
            c = 0
            for i in range(int(self.n / 2)):
                self.means[i] = round((2 * i + 1) * 100 / (2 * int(self.n/2)))
            for i in range(int(self.n / 2), self.n):
                self.means[i] = round(100 - (2 * c + 1) * 100 / (2 * int(self.n/2 +0.5)))
                c += 1
        elif type == "ERR":
            for i in range(self.n):
                self.means[i] = random.randint(30, 70)
        elif type == "SIN":
            for i in range(self.n):
                self.means[i] = round(50 * (1 + math.sin(math.pi * i / 6)))
        return self.means

    # It generates a single value for the demand in period t according to the pdf of d_t
    def gen_demand(self, t):  # t为第t个时期，求最小的需求i，使得需求小于等于i的概率大于等于某个随机概率val
        val = random.random() # 生成[0.0,1.0)范围内的随机浮点数
        pdf = 0.0
        for i in range(0, self.max_demand+1):
            pdf = pdf + self.prob[t][i]
            if pdf >= val:
                return i
        return self.max_demand
