"""Original fixed synthetic controls. No parameter search or external data."""
import json
from pathlib import Path

def s(n, owner, safe, *moves):
    return {'name':n,'owner':owner,'safe':safe,'moves':[{'action':a,'to':t}for a,t in moves]}
def control(id,title,states,goals,why):
    return {'id':id,'title':title,'input':{'arena':{'states':states},'goals':goals},'why':why}
def controls():
    base=[s('choose','controller',True,('wait','choose'),('finish','done')),s('done','environment',True,('after','bad')),s('bad','controller',False,('stay','bad'))]
    env=json.loads(json.dumps(base));env[0]['owner']='environment'
    return [
        control('stall','A winning successor can still stall',base,['done'],'Both wait and finish target winning states. Repeating wait never reaches the goal; finish has worst-case bound of 1. Goal success stops before the after move.'),
        control('owner_flip','The environment can wait forever',env,['done'],'Changing only the owner of choose removes its reach-avoid guarantee. It remains safe-until-goal. No fairness assumption forces finish.'),
        control('detour','A slower policy can still win',[s('start','controller',True,('direct','goal'),('detour','middle')),s('middle','controller',True,('finish','goal')),s('goal','environment',True,('stay','goal'))],['goal'],'The detour is winning in two moves but is not rank-optimal. Not every nonoptimal action causes failure.'),
        control('adversary','Worst case, not a favorable path',[s('start','environment',True,('short','goal'),('long','middle')),s('middle','controller',True,('finish','goal')),s('goal','controller',True,('stay','goal'))],['goal'],'An environment branch of length 2 sets the bound even though a one-step path exists.'),
        control('unsafe_shortcut','Unsafe shortcut is not a reach-avoid route',[s('start','controller',True,('fast','bad'),('review','middle')),s('middle','environment',True,('ok','goal')),s('goal','controller',True,('after','bad')),s('bad','environment',False,('stay','bad'))],['goal'],'A terminal goal may have unsafe outgoing edges, but hitting unsafe before the goal loses.'),
        control('five_steps','A five-move forced arrival',[s('s'+str(i),'controller'if i%2==0 else'environment',True,('next','s'+str(i+1)))for i in range(5)]+[s('s5','environment',True,('stay','s5'))],['s5'],'All five strict rank decreases appear in the complete strategy graph.'),
        control('no_goals','Safe forever is not arrival',[s('idle','controller',True,('wait','idle'))],[],'The empty target loses reach-avoid despite winning safety-until-goal. The single one-action controller assignment is still counted.'),
        control('all_goals','First hit takes zero moves',[s('a','controller',True,('next','b')),s('b','environment',True,('next','a'))],['b','a'],'Both roots succeed immediately. Goal order normalizes to arena order; goal actions are not policy decisions.'),
        control('unreachable','A visible target can be unreachable',[s('idle','environment',True,('wait','idle')),s('goal','controller',True,('stay','goal'))],['goal'],'The complete target-avoiding trap and a lasso show why graph presence does not imply reachability.'),
        control('two_goals','Either terminal goal is enough',[s('choose','environment',True,('left','g1'),('right','g2')),s('g1','controller',True,('after','bad')),s('g2','environment',True,('after','bad')),s('bad','controller',False,('stay','bad'))],['g1','g2'],'Both adversarial branches hit a safe goal in one move. The objective does not require visiting both goals.'),
        control('parallel','Two action assignments, one target behavior',[s('start','controller',True,('a','goal'),('b','goal')),s('goal','environment',True,('stay','goal'))],['goal'],'Policy counts keep distinct action labels even when they have the same target. Counts are not behavior equivalence classes.'),
        control('unsafe_root','An already-unsafe root loses',[s('bad','controller',False,('escape','goal')),s('goal','environment',True,('stay','goal'))],['goal'],'A later safe target cannot repair an unsafe prefix. No move is taken from the unsafe root.')
    ]
if __name__=='__main__':
    dest=Path(__file__).resolve().parents[1]/'docs/reachavoid-controls.json'
    dest.write_text(json.dumps(controls(),indent=2)+'\n')
    dest.with_name('reachavoid-example.json').write_text(json.dumps(controls()[0]['input'],indent=2)+'\n')
