"""
solvers.py - Exact and Baseline Algorithms for Verification and Claims
Implements exact solvers for Tier-S claims and verification routines.
"""

from collections import deque
import heapq
import itertools

def solve_knapsack(capacity, weights, values):
    """Exact 0/1 Knapsack using dynamic programming."""
    dp = [0] * (capacity + 1)
    for w, v in zip(weights, values):
        if w > capacity:
            continue
        for c in range(capacity, w - 1, -1):
            if dp[c - w] + v > dp[c]:
                dp[c] = dp[c - w] + v
    return dp[capacity]

def solve_greedy_knapsack(capacity, weights, values):
    """
    Greedy Knapsack by decreasing value/weight ratio.
    Skips items that do not fit.
    """
    items = []
    for idx, (w, v) in enumerate(zip(weights, values)):
        items.append((v / w, v, w, idx))
    # Sort decreasing by ratio, breaking ties by value descending
    items.sort(key=lambda x: (x[0], x[1]), reverse=True)
    
    total_val = 0
    rem_cap = capacity
    for ratio, v, w, idx in items:
        if w <= rem_cap:
            total_val += v
            rem_cap -= w
    return total_val

def solve_interval_scheduling_count(windows):
    """
    Maximum cardinality compatible windows (touching allowed: finish_1 <= start_2).
    windows: list of (start, finish, value)
    """
    if not windows:
        return 0
    # Sort by finish time ascending, then start time ascending
    sorted_w = sorted(windows, key=lambda x: (x[1], x[0]))
    count = 0
    last_finish = -1
    for s, f, v in sorted_w:
        if s >= last_finish:
            count += 1
            last_finish = f
    return count

def solve_interval_scheduling_weight(windows):
    """
    Maximum total value compatible windows (touching allowed: finish_1 <= start_2).
    windows: list of (start, finish, value)
    """
    if not windows:
        return 0
    sorted_w = sorted(windows, key=lambda x: (x[1], x[0]))
    n = len(sorted_w)
    
    # Precompute predecessors using binary search
    # predecessor of i is the latest j < i with sorted_w[j].finish <= sorted_w[i].start
    # since finish times are sorted:
    starts = [w[0] for w in sorted_w]
    finishes = [w[1] for w in sorted_w]
    
    dp = [0] * (n + 1)
    for i in range(1, n + 1):
        s_i, f_i, v_i = sorted_w[i - 1]
        # Find latest j < i with finishes[j-1] <= s_i
        # Binary search
        low, high = 1, i - 1
        pred = 0
        while low <= high:
            mid = (low + high) // 2
            if finishes[mid - 1] <= s_i:
                pred = mid
                low = mid + 1
            else:
                high = mid - 1
        dp[i] = max(dp[i - 1], v_i + dp[pred])
    return dp[n]

def solve_rod_cutting(prices, L):
    """
    Exact rod cutting (unbounded knapsack) for drum length L.
    prices: dict or list where prices[j] is price of piece of length j (1 <= j <= L)
    """
    dp = [0] * (L + 1)
    for j in range(1, L + 1):
        best = 0
        for i in range(1, j + 1):
            val = prices[i] + dp[j - i]
            if val > best:
                best = val
        dp[j] = best
    return dp[L]

def solve_tsp_manhattan(sites):
    """
    Exact TSP closed Manhattan tour using Held-Karp dynamic programming.
    sites: list of (x, y) coordinates. Starting at site 0.
    """
    n = len(sites)
    if n <= 1:
        return 0
    if n == 2:
        d = abs(sites[0][0] - sites[1][0]) + abs(sites[0][1] - sites[1][1])
        return 2 * d

    dist = [[abs(sites[i][0] - sites[j][0]) + abs(sites[i][1] - sites[j][1])
             for j in range(n)] for i in range(n)]
    
    memo = {}
    def visit(mask, u):
        if mask == (1 << n) - 1:
            return dist[u][0]
        state = (mask, u)
        if state in memo:
            return memo[state]
        ans = 10**9
        for v in range(n):
            if not (mask & (1 << v)):
                res = dist[u][v] + visit(mask | (1 << v), v)
                if res < ans:
                    ans = res
        memo[state] = ans
        return ans

    return visit(1, 0)

def nearest_neighbor_tour_length(sites):
    """
    Nearest neighbor tour length starting from site 0.
    Ties broken by site index.
    """
    n = len(sites)
    if n <= 1:
        return 0
    visited = [False] * n
    visited[0] = True
    curr = 0
    tour = [0]
    total_len = 0
    
    for _ in range(n - 1):
        best_v = None
        best_d = 10**9
        cx, cy = sites[curr]
        for v in range(n):
            if not visited[v]:
                d = abs(cx - sites[v][0]) + abs(cy - sites[v][1])
                if d < best_d:
                    best_d = d
                    best_v = v
        visited[best_v] = True
        total_len += best_d
        curr = best_v
        tour.append(best_v)
        
    # Return to 0
    total_len += abs(sites[curr][0] - sites[0][0]) + abs(sites[curr][1] - sites[0][1])
    return total_len, tour

def solve_min_vertex_cover(num_nodes, edges):
    """
    Exact minimum vertex cover size.
    edges: list of (u, v)
    """
    if not edges:
        return 0
    edge_masks = [(1 << u) | (1 << v) for u, v in edges]
    
    for k in range(1, num_nodes + 1):
        for comb in itertools.combinations(range(num_nodes), k):
            c_mask = 0
            for node in comb:
                c_mask |= (1 << node)
            if all((c_mask & em) for em in edge_masks):
                return k
    return num_nodes

def levenshtein_distance(s1, s2):
    """Exact Levenshtein edit distance between s1 and s2."""
    m, n = len(s1), len(s2)
    prev = list(range(n + 1))
    for i, c1 in enumerate(s1):
        curr = [i + 1] * (n + 1)
        for j, c2 in enumerate(s2):
            curr[j + 1] = min(
                prev[j + 1] + 1,        # deletion from s1
                curr[j] + 1,            # insertion into s1
                prev[j] + (0 if c1 == c2 else 1) # substitution
            )
        prev = curr
    return prev[n]

def count_overlapping_occurrences(text, pattern):
    """Count occurrences of pattern in text, overlaps included."""
    if not pattern or len(pattern) > len(text):
        return 0
    count = 0
    pos = 0
    while True:
        pos = text.find(pattern, pos)
        if pos == -1:
            break
        count += 1
        pos += 1
    return count

def dijkstra_cheapest_cost(source, target, num_nodes, adj, edge_cost_fn):
    """
    Find cheapest route cost from source to target.
    edge_cost_fn(u, v) returns cost of traversing directed edge u -> v.
    """
    dist = {source: 0}
    pq = [(0, source)]
    while pq:
        d, u = heapq.heappop(pq)
        if d > dist[u]:
            continue
        if u == target:
            return d
        for v in adj.get(u, []):
            cost = d + edge_cost_fn(u, v)
            if v not in dist or cost < dist[v]:
                dist[v] = cost
                heapq.heappush(pq, (cost, v))
    return dist.get(target, float('inf'))

def shortest_hop_cost(source, target, num_nodes, adj, edge_cost_fn):
    """
    Find the minimum cost among all routes with the minimum number of road hops from source to target.
    """
    # 1. BFS to find minimum hops
    q = deque([(source, 0)])
    min_hops = {source: 0}
    while q:
        u, h = q.popleft()
        if u == target:
            break
        for v in adj.get(u, []):
            if v not in min_hops:
                min_hops[v] = h + 1
                q.append((v, h + 1))
    
    if target not in min_hops:
        return float('inf')
        
    target_hops = min_hops[target]
    
    # 2. Find min cost among all paths of exactly min_hops
    # Using DP: dp[hop][u] = min cost to reach u in `hop` hops
    dp = {0: {source: 0}}
    for h in range(target_hops):
        dp[h + 1] = {}
        for u, c in dp[h].items():
            for v in adj.get(u, []):
                if min_hops.get(v) == h + 1: # only forward along shortest hop DAG
                    cost = c + edge_cost_fn(u, v)
                    if v not in dp[h + 1] or cost < dp[h + 1][v]:
                        dp[h + 1][v] = cost
                        
    return dp[target_hops].get(target, float('inf'))

