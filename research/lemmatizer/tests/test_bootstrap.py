import sys
from pathlib import Path
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from bootstrap_evaluation import prepare, weighted_scores
from evaluate_clusters import cluster_scores


class BootstrapTests(unittest.TestCase):
    def test_weights_match_explicit_resampling_with_cross_group_merge(self):
        rows=[{'target_id':str(i),'gold_cluster':g} for i,g in enumerate(['a','a','b','b','c','c'])]
        preds={str(i):{'status':'ok' if p else 'abstained','pred_cluster':p} for i,p in enumerate(['x',None,'x','y','z','z'])}
        groups=['a','b','c']
        data=prepare(rows,preds,groups)
        for weights in [np.array([1,1,1]),np.array([2,1,0]),np.array([0,0,3])]:
            gold=[]; labels=[];covered=0
            for r in rows:
                count=weights[groups.index(r['gold_cluster'])]
                p=preds[r['target_id']]
                label=('lemma',p['pred_cluster']) if p['status']=='ok' else ('abstention',r['target_id'])
                gold.extend([r['gold_cluster']]*count);labels.extend([label]*count)
                covered+=count*(p['status']=='ok')
            expected=cluster_scores(gold,labels)['bcubed']
            np.testing.assert_allclose(weighted_scores(data,weights),[expected[k] for k in ['precision','recall','f1']]+[covered/len(gold)])

    def test_perfect_partition_remains_perfect(self):
        rows=[{'target_id':str(i),'gold_cluster':str(i//2)} for i in range(6)]
        preds={r['target_id']:{'status':'ok','pred_cluster':r['gold_cluster']} for r in rows}
        np.testing.assert_allclose(weighted_scores(prepare(rows,preds,['0','1','2']),np.array([2,0,1])),np.ones(4))
