"""Four continuous-space scenarios. Coordinates are floating-point (x, y)."""
SCENARIOS={
 '1. Normal Escape': {'kind':'Working','description':'Collect a resource, then navigate continuously to rescue while zombies pursue.','zombies':[('Z1',(12.0,3.5)),('Z2',(8.0,11.5))],'survivors':[('S1',(2.0,1.5),'Water'),('S2',(6.5,1.5),'Food'),('S3',(1.5,13.0),'Medicine')],'time_limit':260},
 '2. Close Encounter': {'kind':'Working','description':'A zombie begins nearby; survivors replan continuously to avoid distance-based capture.','zombies':[('Z1',(8.0,2.0)),('Z2',(11.5,11.0))],'survivors':[('S1',(6.5,2.0),'Food'),('S2',(2.0,8.0),'Medicine'),('S3',(1.5,13.0),'Medicine')],'time_limit':220},
 '3. Resource Detour': {'kind':'Working','description':'Survivors travel to separated resources and route around rectangular obstacles.','zombies':[('Z1',(12.0,4.0)),('Z2',(8.0,10.5))],'survivors':[('S1',(1.5,2.0),'Medicine'),('S2',(6.5,1.5),'Water'),('S3',(1.5,12.0),'Food')],'time_limit':280},
 '4. Emergency Outbreak': {'kind':'Working','description':'S1 is infected at step 45 and becomes an additional zombie, changing the threat.','zombies':[('Z1',(12.0,3.5)),('Z2',(8.0,11.5))],'survivors':[('S1',(10.5,3.5),'Water'),('S2',(6.5,1.5),'Food'),('S3',(1.5,13.0),'Medicine')],'infection':{'sid':'S1','step':45},'time_limit':250},
}
