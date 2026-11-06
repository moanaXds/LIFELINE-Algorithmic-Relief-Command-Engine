"""
algos.py - Independent algorithmic primitives for LIFELINE Phase 1 Validator.

All algorithms are implemented from first principles using Python standard library:
1. Graph algorithms:
   - Breadth-First Search (BFS) for connectivity and fewest-hops paths.
   - Dijkstra's Algorithm using heapq for cheapest weighted paths.
   - Double-sweep BFS for diameter / longest shortest path.
2. String algorithms:
   - Overlapping pattern frequency counting.
   - Levenshtein Edit Distance dynamic programming table.
3. Optimization & Decision algorithms:
   - 0/1 Knapsack exhaustive subset search (Tier S).
   - 0/1 Knapsack dynamic programming (for Trap 47 ratio check).
   - Interval Scheduling exhaustive search for max count and max value.
   - Rod / Drum cutting dynamic programming.
   - Traveling Salesperson Problem (TSP) exhaustive permutation search for closed Manhattan tour.
   - Minimum Vertex Cover exhaustive subset search.

Viva Note:
Each algorithm is written with clean loops, standard data structures (queues, heaps, dicts),
and clear invariants so it can be easily explained during viva examination.
"""

from collections import deque
import heapq
import itertools


# =====================================================================
# 1. GRAPH ALGORITHMS
# =====================================================================

def is_graph_connected(num_nodes, edges, start_node=0):
    """
    Checks if an undirected graph on nodes 0..num_nodes-1 is connected
    via standard Breadth-First Search (BFS) starting at start_node.
    
    Returns:
        (bool, set): True if all nodes reachable, plus set of reachable nodes.
    """
    if num_nodes <= 1:
        return True, {0} if num_nodes == 1 else set()

    adj = {i: [] for i in range(num_nodes)}
    for u, v in edges:
        adj[u].append(v)
        adj[v].append(u)

    visited = {start_node}
    queue = deque([start_node])
    while queue:
        curr = queue.popleft()
        for neighbor in adj[curr]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)

    return len(visited) == num_nodes, visited


def bfs_hops_from_source(num_nodes, edges, source=0):
    """
    Computes shortest hop count (unweighted distance) from source to all nodes
    using layered BFS.
    
    Returns:
        dict: mapping node -> hop distance (only for reachable nodes).
    """
    adj = {i: [] for i in range(num_nodes)}
    for u, v in edges:
        adj[u].append(v)
        adj[v].append(u)

    dist = {source: 0}
    queue = deque([source])
    while queue:
        u = queue.popleft()
        for v in adj[u]:
            if v not in dist:
                dist[v] = dist[u] + 1
                queue.append(v)
    return dist


def dijkstra_cheapest_paths(num_nodes, road_list, location_penalties, source=0):
    """
    Computes cheapest path costs from source to all nodes using Dijkstra's algorithm.
    Step cost from u to v is: road_minutes + location_penalty of v.
    
    Args:
        num_nodes (int): Number of locations V.
        road_list (list of dict): roads with 'u', 'v', 'minutes'.
        location_penalties (dict): loc_id -> penalty.
        source (int): start node (HQ = 0).
        
    Returns:
        dict: loc_id -> minimum cost from source.
    """
    adj = {i: [] for i in range(num_nodes)}
    for r in road_list:
        u, v, m = r['u'], r['v'], r['minutes']
        # Directed step cost u -> v is m + pen(v)
        cost_uv = m + location_penalties.get(v, 0)
        cost_vu = m + location_penalties.get(u, 0)
        adj[u].append((v, cost_uv))
        adj[v].append((u, cost_vu))

    dist = {i: float('inf') for i in range(num_nodes)}
    dist[source] = 0
    pq = [(0, source)]

    while pq:
        d, u = heapq.heappop(pq)
        if d > dist[u]:
            continue
        for v, step_cost in adj[u]:
            new_d = d + step_cost
            if new_d < dist[v]:
                dist[v] = new_d
                heapq.heappush(pq, (new_d, v))

    return dist


def min_cost_among_fewest_roads(num_nodes, road_list, location_penalties, source, target):
    """
    Finds the minimum step-cost among all routes that achieve the minimum number
    of roads (hops) from source to target.
    
    Algorithm:
    1. Layered BFS from source to find exact hop distance to all nodes.
    2. BFS backward/forward DAG of shortest-hop edges, finding minimum cost
       to target along DAG paths.
    """
    adj = {i: [] for i in range(num_nodes)}
    for r in road_list:
        u, v, m = r['u'], r['v'], r['minutes']
        adj[u].append((v, m + location_penalties.get(v, 0)))
        adj[v].append((u, m + location_penalties.get(u, 0)))

    # Step 1: Hop distance via BFS
    hops = {source: 0}
    q = deque([source])
    while q:
        u = q.popleft()
        for v, _ in adj[u]:
            if v not in hops:
                hops[v] = hops[u] + 1
                q.append(v)

    if target not in hops:
        return float('inf')  # Unreachable

    target_hops = hops[target]

    # Step 2: Dynamic programming over BFS layers
    # min_cost[u] = minimum cost to reach u in hops[u] steps
    min_cost = {i: float('inf') for i in range(num_nodes)}
    min_cost[source] = 0

    # Sort nodes by increasing hop distance
    nodes_by_hop = sorted(hops.keys(), key=lambda x: hops[x])
    for u in nodes_by_hop:
        if hops[u] >= target_hops:
            continue
        curr_cost = min_cost[u]
        if curr_cost == float('inf'):
            continue
        for v, step_cost in adj[u]:
            if hops[v] == hops[u] + 1:
                if curr_cost + step_cost < min_cost[v]:
                    min_cost[v] = curr_cost + step_cost

    return min_cost[target]


def double_sweep_bfs(num_nodes, edges):
    """
    Double-sweep BFS algorithm for approximating / lower-bounding graph diameter.
    1. BFS from arbitrary node (0) to find farthest node u.
    2. BFS from u to find farthest node v.
    The distance d(u, v) is a proven lower bound on the graph diameter.
    
    Returns:
        int: Longest hop distance found between two nodes.
    """
    if num_nodes <= 1:
        return 0

    adj = {i: [] for i in range(num_nodes)}
    for u, v in edges:
        adj[u].append(v)
        adj[v].append(u)

    def bfs_farthest(start):
        dist = {start: 0}
        q = deque([start])
        farthest_node = start
        max_dist = 0
        while q:
            curr = q.popleft()
            d = dist[curr]
            if d > max_dist:
                max_dist = d
                farthest_node = curr
            for nxt in adj[curr]:
                if nxt not in dist:
                    dist[nxt] = d + 1
                    q.append(nxt)
        return farthest_node, max_dist

    node_u, _ = bfs_farthest(0)
    _, diam = bfs_farthest(node_u)
    return diam


# =====================================================================
# 2. STRING ALGORITHMS
# =====================================================================

def count_pattern_overlaps(text, pattern):
    """
    Counts all occurrences of pattern in text, including overlapping matches.
    Example: text='AAAA', pattern='AA' -> returns 3.
    """
    if not pattern or not text or len(pattern) > len(text):
        return 0
    count = 0
    p_len = len(pattern)
    for i in range(len(text) - p_len + 1):
        if text[i:i + p_len] == pattern:
            count += 1
    return count


def levenshtein_distance(str_a, str_b):
    """
    Computes the minimum number of insertions, deletions, and substitutions
    to transform str_a into str_b using dynamic programming table of size (M+1) x (N+1).
    """
    m, n = len(str_a), len(str_b)
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j

    for i in range(1, m + 1):
        char_a = str_a[i - 1]
        for j in range(1, n + 1):
            char_b = str_b[j - 1]
            cost = 0 if char_a == char_b else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,       # Deletion from str_a
                dp[i][j - 1] + 1,       # Insertion into str_a
                dp[i - 1][j - 1] + cost # Substitution
            )
    return dp[m][n]


# =====================================================================
# 3. OPTIMIZATION & CLAIMS ALGORITHMS
# =====================================================================

def knapsack_01_exhaustive(weights, values, capacity):
    """
    Finds the exact optimal total value for 0/1 knapsack using exhaustive search
    over all 2^N subsets of items (Tier S has N <= 20).
    """
    n = len(weights)
    best_value = 0

    # Recursive branch-and-bound or combinations search
    def branch(idx, current_weight, current_value):
        nonlocal best_value
        if current_weight > capacity:
            return
        if current_value > best_value:
            best_value = current_value
        if idx == n:
            return
        
        # Upper bound prune: if current + remaining values <= best_value, prune
        rem_sum = sum(values[idx:])
        if current_value + rem_sum <= best_value:
            return

        # Try including item idx
        branch(idx + 1, current_weight + weights[idx], current_value + values[idx])
        # Try excluding item idx
        branch(idx + 1, current_weight, current_value)

    branch(0, 0, 0)
    return best_value


def knapsack_01_dp(weights, values, capacity):
    """
    Standard dynamic programming solution for 0/1 Knapsack problem.
    Used for larger cases (e.g., Trap 47 verification where N <= 60).
    """
    n = len(weights)
    dp = [0] * (capacity + 1)
    for i in range(n):
        w, v = weights[i], values[i]
        for c in range(capacity, w - 1, -1):
            if dp[c - w] + v > dp[c]:
                dp[c] = dp[c - w] + v
    return dp[capacity]


def greedy_knapsack_value(crate_records, capacity):
    """
    Executes greedy knapsack heuristic:
    - Sorts crates by decreasing value per kg (exact cross-multiplication: v1*w2 vs v2*w1).
    - Ties broken by smaller crate_id.
    - Takes crates greedily, skipping those that do not fit.
    Returns total value achieved.
    """
    class CrateItem:
        def __init__(self, crid, w, v):
            self.crid = crid
            self.w = w
            self.v = v

        def __lt__(self, other):
            # v/w > other.v/other.w <=> v * other.w > other.v * w
            cross_self = self.v * other.w
            cross_other = other.v * self.w
            if cross_self != cross_other:
                return cross_self > cross_other  # Decreasing order
            return self.crid < other.crid       # Increasing crate_id on tie

    items = [CrateItem(c['crate_id'], c['weight'], c['value']) for c in crate_records]
    items.sort()

    rem_cap = capacity
    total_val = 0
    for item in items:
        if item.w <= rem_cap:
            rem_cap -= item.w
            total_val += item.v

    return total_val


def interval_scheduling_exhaustive(intervals):
    """
    Computes exact optimal compatible window count and max total value.
    Touching windows ARE compatible (finish_1 <= start_2).
    
    Args:
        intervals (list of tuple): (start, finish, value)
        
    Returns:
        (int, int): (window_count_opt, window_value_opt)
    """
    if not intervals:
        return 0, 0

    # Sort intervals by finish time
    sorted_int = sorted(intervals, key=lambda x: (x[1], x[0]))
    n = len(sorted_int)

    # 1. Optimal count (Greedy Earliest Finish Time with touching allowed: s >= prev_f)
    curr_f = -1
    opt_count = 0
    for s, f, _ in sorted_int:
        if s >= curr_f:
            opt_count += 1
            curr_f = f

    # 2. Optimal value (Weighted interval scheduling DP)
    # p[i] = latest non-overlapping interval j before i (such that sorted_int[j].finish <= sorted_int[i].start)
    dp_val = [0] * (n + 1)
    for i in range(1, n + 1):
        s_i, f_i, v_i = sorted_int[i - 1]
        # Find latest j < i with finish <= s_i
        latest_j = 0
        for j in range(i - 1, 0, -1):
            if sorted_int[j - 1][1] <= s_i:
                latest_j = j
                break
        dp_val[i] = max(dp_val[i - 1], v_i + dp_val[latest_j])

    return opt_count, dp_val[n]


def rod_cutting_exhaustive(drum_length, prices_dict):
    """
    Computes exact optimal revenue from cutting a drum of length L into pieces,
    where price of piece of length j is prices_dict[j].
    """
    dp = [0] * (drum_length + 1)
    for l in range(1, drum_length + 1):
        max_val = 0
        for cut in range(1, l + 1):
            if cut in prices_dict:
                max_val = max(max_val, prices_dict[cut] + dp[l - cut])
        dp[l] = max_val
    return dp[drum_length]


def tsp_closed_manhattan_exhaustive(coords):
    """
    Computes exact optimal closed Manhattan tour length visiting all sites
    starting at site 0 via exhaustive permutation search.
    coords: list of (x, y) coordinates for sites 0..n-1 (n <= 9 for Tier S).
    """
    n = len(coords)
    if n <= 1:
        return 0

    def manhattan(p1, p2):
        return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])

    best_len = float('inf')
    # Permute sites 1 to n-1 (site 0 is fixed at start)
    for perm in itertools.permutations(range(1, n)):
        tour = (0,) + perm
        cost = 0
        for i in range(n - 1):
            cost += manhattan(coords[tour[i]], coords[tour[i + 1]])
        cost += manhattan(coords[tour[-1]], coords[0])
        if cost < best_len:
            best_len = cost

    return best_len


def vertex_cover_min_exhaustive(num_nodes, edges):
    """
    Computes minimum vertex cover size by testing node subsets of increasing
    cardinality k = 1, 2, ... until a subset touches every edge in edges.
    num_nodes <= 14 for Tier S.
    """
    if not edges:
        return 0

    for k in range(1, num_nodes + 1):
        for comb in itertools.combinations(range(num_nodes), k):
            cset = set(comb)
            if all(u in cset or v in cset for u, v in edges):
                return k
    return num_nodes

