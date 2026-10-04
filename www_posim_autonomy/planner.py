"""Small sensor-only occupancy planner for the two-buoy teaching example.

Input consists of measured laser endpoints. It never loads world obstacles.
This deliberately simple static-grid planner is not a maritime COLREG planner.
"""
import heapq
import math

class LaserPlanner:
    def __init__(self,origin,resolution=1.,clearance=4.):
        self.origin=origin;self.resolution=resolution;self.clearance=clearance
        self.occupied=set();self.inflated=set();self.revision=0
    def cell(self,p):return tuple(round((p[i]-self.origin[i])/self.resolution) for i in (0,1))
    def point(self,c):return tuple(self.origin[i]+c[i]*self.resolution for i in (0,1))
    def observe(self,endpoints):
        cells={self.cell(p) for p in endpoints};new=cells-self.occupied
        if not new:return
        self.occupied.update(new);n=math.ceil(self.clearance/self.resolution)
        offsets=[(i,j) for i in range(-n,n+1) for j in range(-n,n+1) if math.hypot(i,j)*self.resolution<=self.clearance]
        self.inflated.update((c[0]+i,c[1]+j) for c in new for i,j in offsets);self.revision+=1
    def clear_segment(self,a,b):
        distance=math.dist(a,b);n=max(1,math.ceil(distance/(self.resolution*.3)))
        return all(self.cell((a[0]+(b[0]-a[0])*i/n,a[1]+(b[1]-a[1])*i/n)) not in self.inflated for i in range(n+1))
    def plan(self,start,goal):
        source,target=self.cell(start),self.cell(goal)
        if source in self.inflated or target in self.inflated:return []
        q=[(0,source)];cost={source:0};prev={};bounds=(-15,60,-35,35)
        while q:
            _,u=heapq.heappop(q)
            if u==target:
                path=[u]
                while path[-1]!=source:path.append(prev[path[-1]])
                return [self.point(c) for c in reversed(path)]
            for dx,dy in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
                v=(u[0]+dx,u[1]+dy)
                if v in self.inflated or not bounds[0]<=v[0]<=bounds[1] or not bounds[2]<=v[1]<=bounds[3]:continue
                if dx and dy and ((u[0]+dx,u[1]) in self.inflated or (u[0],u[1]+dy) in self.inflated):continue
                g=cost[u]+math.hypot(dx,dy)
                if g>=cost.get(v,float('inf')):continue
                cost[v]=g;prev[v]=u;heapq.heappush(q,(g+math.dist(v,target),v))
        return []

def yaw(q):return math.atan2(2*(q.w*q.z+q.x*q.y),1-2*(q.y*q.y+q.z*q.z))

def steering(position,heading,path,max_speed=.8):
    if not path:return 0.,0.
    # Look ahead only along a safe connected path; large lookahead cuts corners.
    closest=min(range(len(path)),key=lambda i:math.dist(position,path[i]));target=path[min(len(path)-1,closest+2)]
    error=(math.atan2(target[1]-position[1],target[0]-position[0])-heading+math.pi)%(2*math.pi)-math.pi
    turn=max(-.35,min(.35,1.2*error))
    speed=max_speed*max(0.,math.cos(error))**4 if abs(error)<.6 else 0.
    return speed,turn
