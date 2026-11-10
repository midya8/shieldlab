"""Original supplied controls for the safe recurrent-target extension."""
from pathlib import Path
import json


def request(rows, goals):
    return {'arena': {'states': [{'name': n, 'owner': p, 'safe': safe,
            'moves': [{'action': a, 'to': t} for a, t in moves]} for n, p, safe, moves in rows]}, 'goals': goals}


def controls():
    c = 'controller';e = 'environment'
    rows = [
        ('first_visit', 'One acknowledgement is not recurrence', 'The first target visit succeeds in the old stopping game. The live outgoing target edge then enters a permanent safe wait.',
         [('start', c, True, [('send','ack')]), ('ack', e, True, [('leave','idle')]), ('idle', e, True, [('wait','idle')])], ['ack'], []),
        ('controlled_return', 'Control the return', 'The target controller can return instead of drain. It must keep choosing return on every visit.',
         [('start', c, True, [('wait','start'), ('send','ack')]), ('ack', c, True, [('return','start'),('drain','idle')]), ('idle', e, True, [('wait','idle')])], ['ack'], ['start','ack']),
        ('adversarial_return', 'Same graph, different owner', 'Change only the target owner. The environment may drain into a target-free cycle; no fairness rescues the controller.',
         [('start', c, True, [('wait','start'), ('send','ack')]), ('ack', e, True, [('return','start'),('drain','idle')]), ('idle', e, True, [('wait','idle')])], ['ack'], []),
        ('nonbottom_cycle', 'An exit is not an obligation', 'Both states are in one target-containing SCC. The environment can keep taking the target-free wait rather than the exit.',
         [('wait', e, True, [('stay','wait'),('visit','goal')]),('goal',e,True,[('return','wait')])], ['goal'], []),
        ('unsafe_after_goal', 'Success does not stop this game', 'The goal outgoing edge is a safety obligation under recurrence, unlike first-hit reach-avoid.',
         [('goal',c,True,[('leave','bad')]),('bad',e,False,[('reset','goal')])], ['goal'], []),
        ('goal_self_loop', 'One state, infinitely many visits', 'A safe target self-loop wins; recurrence does not require distinct targets or nontrivial travel.',
         [('goal',e,True,[('again','goal')])], ['goal'], ['goal']),
        ('empty_targets', 'Safe forever, never a target', 'No target makes recurrence impossible even when every state is safe.',
         [('safe',c,True,[('wait','safe')])], [], []),
        ('all_targets', 'Every step is a target', 'With all states safe and targets, every play wins recurrence.',
         [('a',e,True,[('stay','a'),('switch','b')]),('b',c,True,[('back','a')])], ['b','a'], ['a','b']),
        ('unsafe_root', 'A future goal cannot erase a leak', 'An unsafe state fails immediately even if it can move into an otherwise safe recurrent goal.',
         [('bad',c,False,[('repair','goal')]),('goal',e,True,[('stay','goal')])], ['goal'], ['goal']),
        ('mixed_stalling', 'Winning targets are not a progress shield', 'Every safe state is winning. Repeatedly selecting within-region detours can still produce a target-free cycle.',
         [('a',c,True,[('detour','b'),('visit','goal')]),('b',c,True,[('detour','a'),('visit','goal')]),('goal',e,True,[('return','a')])], ['goal'], ['a','b','goal']),
        ('six_ring', 'A full six-state return', 'Every forced turn remains safe and reaches the target repeatedly, with alternating owners.',
         [('s'+str(i),c if i%2 else e,True,[('next','s'+str((i+1)%6))]) for i in range(6)], ['s5'], ['s'+str(i) for i in range(6)]),
        ('unreachable_goal', 'A disconnected target changes nothing', 'The supplied target exists but a separate waiting component cannot reach it.',
         [('wait',c,True,[('stay','wait')]),('goal',e,True,[('stay','goal')])], ['goal'], ['goal']),
    ]
    return [{'id': i, 'name': name, 'description': desc, 'input': request(rows, goals), 'expected_winning': win}
            for i, name, desc, rows, goals, win in rows]


if __name__ == '__main__':
    root = Path(__file__).resolve().parents[1]
    (root/'docs/recurrence-controls.json').write_text(json.dumps(controls(), indent=2)+'\n')
