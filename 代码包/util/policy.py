
class InventoryPolicy:
    def __init__(self):
        # Name of the policy
        self.name = "policy"
        #时间范围内的总时间段数
        self.n = 1  
        # 订单类型 如果是动态则 "dynamic", 例如(s, S) (R,S)策略
        # 如果是静态则 "static", 例如 (R, Q)
        self.order_quantity_type = "dynamic"

        # n维向量，取值为0或1，R(i)=1表示第i个时间段开始时需要进行审查，反之不用检查
        self.R = []

        # n维向量，即s
        self.s = []

        # n维向量，即S
        self.S = []

        # n维向量，即订单数Q
        self.Q = []

        # 预期总成本
        self.expected_cost = 0

        # 分支定界法里的修剪率，pruning_count是修剪次数，这个percentage=count/(2^(n+1)-1)
        self.pruning_percentage = 0
