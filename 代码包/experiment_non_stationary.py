import time
import random
from util import instance
from util import policy as pol
from util import simulator
from solvers.RsS import rss_branch_and_bound_sdp, rss_brute_force_baseline, rss_binary_tree_sdp, rss_sdp_kconv_memo,rss_sdp,rss_heuristic_sdp


# use these list of seeds to make the simulation replicable. The simulation number is the length
# of this list
seed = 1989
random.seed(seed)
n = 12
simulate = True
runs = 100

# generate and instance of the RsS problem
inst = instance.InventoryInstance()
inst.n = n                              # number of periods
inst.ch = 1                             # holding cost
inst.cp = 10                             # penalty cost
inst.cl = 0                          # linear ordering cost
inst.co = 80                            # order cost
inst.cr = 200                            # review cost
inst.init_inv = 0                       # initial inventory
means = inst.gen_means("ERR")
inst.cv = 0.4                           # coefficient of variation of the normal distributions
inst.means = means
threshold = 0.001

inst.gen_non_stationary_poisson_demand(0,threshold)
inst.max_inv_bouding(threshold)
inst.probability_convolution()
print(means)
print(sum(means)/n)
print("Max_demand = " + str(inst.max_demand))
print("Max_inventory = " + str(inst.max_inv_level))

### SOLVING ###

policies = []
solvers = []

## Baseline
# sol=rss_brute_force_baseline.RsS_BruteForceBaseline()
# solvers.append(sol)

## Binary tree
#sol=rss_binary_tree_sdp.RsS_BinaryTreeSDP()
#solvers.append(sol)

## B&B
# sol=rss_branch_and_bound_sdp.RsS_BranchAndBound()
# solvers.append(sol)

## B&B random
sol = rss_branch_and_bound_sdp.RsS_BranchAndBound()
sol.use_random = True
solvers.append(sol)

## SDP-kconv
sol = rss_sdp_kconv_memo.RsS_SDP_KConv_Memo()
solvers.append(sol)

##SDp
sol = rss_heuristic_sdp.RsS_HeuristicSPSDP()
solvers.append(sol)

## rss-sdp
#sol = rss_sdp.RsS_SDP()
#solvers.append(sol)

print("\n######################"
      "\nSTARTING SOLVING PHASE"
      "\n######################")

for s in solvers:
    print("\nStarting " + s.name)
    start_time = time.time()
    policy = s.solve(inst)
    end_time = time.time() - start_time
    print("Solved in:\t" + str(round(end_time, 2)))
    print("Cost:\t\t" + str(round(policy.expected_cost, 2)))
    print("Reviews:\t" + str(policy.R))
    print("s:\t\t\t" + str(policy.s))
    print("S:\t\t\t" + str(policy.S))
    print("P_perc:\t\t" + str(round(policy.pruning_percentage*100,2)))
    policies.append(policy)

if simulate:
    print("\n#########################"
          "\nSTARTING SIMULATING PHASE"
          "\n#########################")

    print("\nNumber of runs: " + str(runs))
    sim = simulator.Simulator()
    sim.instance = inst
    for p in policies:
        sim.policy = p  ##C_min
        cost = sim.multiple_simulations(runs, seed) ##现实模拟
        act_cost = sim.calc_expected_cost()  ##期望
        print("\nSimulate policy " + p.name)
        print("Expected cost:\t" + str(round(p.expected_cost, 2)))  ##算法的最小
        print("Actual cost:\t" + str(round(act_cost, 2)))  ##C_1(I0)
        print("Observed cost:\t" + str(round(cost, 2)))  ##现实模拟
