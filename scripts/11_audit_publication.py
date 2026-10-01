"""Audit every current result/table and verify plotted quantities without API calls."""
from pathlib import Path
import hashlib
import json
import sys
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.config import questions
from src.metrics import js_divergence


def main():
    results=Path('results'); inventory=[]; checks=[]
    def check(label, test):
        if not bool(test): raise AssertionError(label)
        checks.append(label)
    json_inventory=[]
    for f in sorted(results.rglob('*.json')):
        if f.name=='publication_audit.json':continue
        data=json.loads(f.read_text())
        check(f'{f}: valid JSON',isinstance(data,(list,dict)))
        json_inventory.append({'file':str(f),'sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
    for f in sorted(results.rglob('*.csv')):
        df=pd.read_csv(f)
        numeric=df.select_dtypes(include=np.number)
        check(f'{f}: no infinite numeric values', not np.isinf(numeric.to_numpy()).any())
        inventory.append({'file':str(f),'rows':len(df),'columns':list(df.columns),
                          'missing_by_column':{k:int(v) for k,v in df.isna().sum().items() if v},
                          'identical_rows':int(df.duplicated().sum()),
                          'sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
    m=pd.read_csv(results/'country_item_metrics.csv')
    check('Unique country/item/model/representation metric keys',not m.duplicated(['country','item','condition','representation']).any())
    for col in ['js','tv','wasserstein','human_entropy','model_entropy','entropy_abs_error']:
        s=m[col].dropna();check(f'{col}: within [0,1]',s.between(-1e-12,1+1e-12).all())
    check('Argmax entropy is zero',np.allclose(m[m.representation=='argmax'].model_entropy,0))
    check('Signed entropy equals model minus human',np.allclose(m.entropy_signed_error,m.model_entropy-m.human_entropy))
    # Round-trip parsing preserves distinctions at floating precision in argmax
    # near-ties (e.g. 0.351 versus 0.35100000000000003).
    h=pd.read_csv('data/processed/human_country_distributions.csv',float_precision='round_trip')
    a=pd.read_csv(results/'model_mean_probabilities.csv',float_precision='round_trip')
    for name,df,keys in [('human',h,['country','item']),('model',a,['condition','country','item'])]:
        check(f'{name} probabilities sum to one',np.allclose(df.groupby(keys).p.sum(),1,atol=1e-10))
        check(f'{name} probabilities are nonnegative',df.p.ge(0).all())
    # Recompute all full/argmax JSDs directly from the archived semantic vectors.
    human={k:g.set_index(g.response.astype(str)).p.to_dict() for k,g in h.groupby(['country','item'])}
    machine={k:g.set_index(g.response.astype(str)).p.to_dict() for k,g in a.groupby(['condition','country','item'])}
    errors=[];qs=questions()
    for row in m.itertuples():
        codes=list(map(str,qs[row.item]['human_codes']))
        hp=np.array([human[(row.country,row.item)].get(k,0) for k in codes]);mp=np.array([machine[(row.condition,row.country,row.item)].get(k,0) for k in codes])
        if row.representation=='argmax':
            idx=mp.argmax();mp=np.zeros_like(mp);mp[idx]=1
        errors.append(abs(js_divergence(hp,mp)-row.js))
    check('All country-item JSDs agree with archived probability vectors',max(errors)<1e-12)
    coords=pd.read_csv(results/'cultural_map_coordinates.csv')
    keys=['condition','representation','country']
    check('Unique cultural-map coordinates',not coords.duplicated(keys).any())
    xy=coords.set_index(keys)[['survival_self_expression','traditional_secular']]
    distances=pd.read_csv(results/'cultural_map_distances.csv')
    for row in distances.itertuples():
        calc=np.linalg.norm(xy.loc[(row.condition,row.representation,row.country)].values-xy.loc[('human','expected',row.country)].values)
        check(f'Map distance {row.condition}/{row.representation}/{row.country}',np.isclose(calc,row.distance))
    prompt=pd.read_csv(results/'cultural_map_prompting_distances.csv')
    check('Prompting improvement is paired distance difference',np.allclose(prompt.distance_improvement,prompt.unconditioned_distance-prompt.country_conditioned_distance))
    check('Prompting improvement flags agree',np.array_equal(prompt.improved.values,prompt.distance_improvement.gt(0).values))
    ps=pd.read_csv(results/'population_specificity_metrics.csv')
    check('Default gain is correctly signed',np.allclose(ps.gain_vs_default_js,ps.default_model_js-ps.country_model_js))
    check('LOCO gain is correctly signed',np.allclose(ps.gain_vs_loco_human_js,ps.loco_human_js-ps.country_model_js))
    for fn,count_col,value in [('prompt_sensitivity.csv','n_variants_retained','js_to_condition_mean'),('openai_label_sensitivity.csv','n_label_repetitions_retained','js_to_label_mean')]:
        d=pd.read_csv(results/fn)
        check(f'{fn}: singleton sensitivity is undefined',d.loc[d[count_col]<2,value].isna().all())
    order=pd.read_csv(results/'option_order_metrics.csv')
    check('Every option-order comparison uses reference 0',order.reference_rep.eq(0).all())
    usage=json.loads((results/'api_usage_totals.json').read_text());req=pd.read_csv(results/'api_request_usage.csv')
    check('API request count matches deduplicated ledger',usage['requests']==len(req))
    for col in ['input_tokens','output_tokens','total_tokens','estimated_total_cost_usd']:
        check(f'API {col} total agrees',np.isclose(usage[col],req[col].sum()))
    figs=json.loads(Path('figures/manifest.json').read_text())
    revision=json.loads((results/'revision_analysis_manifest.json').read_text())
    check('Revision analysis completed',revision['completed'])
    expected_si=14+int(revision.get('temporal_targets')=='completed')+int(revision.get('human_sampling')=='completed')
    check('Complete canonical three main figures',figs['main_figures']==3 and len([s for s in figs['figures'] if not s.startswith('figure_s')])==3)
    check('All available supplementary figures exported',figs['supplementary_figures']==expected_si and len(figs['figures'])==3+expected_si)
    direction=pd.read_csv(results/'cultural_deviation_alignment.csv')
    summary=pd.read_csv(results/'cultural_deviation_summary.csv').set_index('condition')
    check('Direction keys are unique',not direction.duplicated(['condition','country','item']).any())
    check('Cosine values lie between -1 and 1',direction.cosine_similarity.dropna().between(-1,1).all())
    for condition,g in direction.groupby('condition'):
        g=g[g.direction_correct.notna()]
        check(f'{condition}: direction fraction recomputed',np.isclose(summary.loc[condition,'direction_correct_percent'],100*g.direction_correct.mean()))
        check(f'{condition}: pooled projection is ratio of sums',np.isclose(summary.loc[condition,'projection_pooled'],g.dot_product.sum()/g.human_shift_sq.sum()))
    loio=pd.read_csv(results/'entropy_leave_one_item_out.csv')
    for condition,g in loio.groupby('condition'):
        check(f'{condition}: all nine leave-one-item-out fits',len(g)==10 and set(g[g.omitted_item.ne('none')].omitted_item)==set(questions())-{'Y003'})
    if revision.get('sample_diagnostics')=='completed':
        sample=pd.read_csv(results/'human_country_year_sample_sizes.csv')
        check('Kish sample diagnostics recompute',np.allclose(sample.kish_n_eff,sample.sum_weight**2/sample.sum_weight_sq))
        check('Kish effective n never exceeds raw n',sample.kish_n_eff.le(sample.raw_n+1e-7).all())
    if revision.get('human_sampling')=='completed':
        sampling=pd.read_csv(results/'human_sampling_sensitivity.csv')
        check('Every human-sampling summary has 1000 valid replicates',sampling.valid_replicates.eq(revision['configuration']['human_sampling']['bootstrap_reps']).all())
        check('Human sampling keeps observed-cell coverage fixed',sampling.min_cells.eq(sampling.max_cells).all())
    for stem in figs['figures']:
        for ext in figs['formats']:check(f'Export {stem}.{ext} exists',(Path('figures')/f'{stem}.{ext}').stat().st_size>100)
    label=json.loads((results/'figure1_label_audit.json').read_text())
    check('Figure 1 labels cover no points or other labels',label['point_overlaps']==label['label_overlaps']==0)
    report={'passed':True,'n_checks':len(checks),'checks':checks,'result_inventory':inventory,'json_inventory':json_inventory,
            'interpretation_notes':[
              'Wasserstein is undefined for unordered A165.',
              'Prompt/label singleton groups remain in diagnostic files with undefined sensitivity.',
              'No retained Sol F120 order-0 reference: order sensitivity is not estimable for that item.',
              'Sol entropy CIs use only nine item clusters and asymptotic normal critical values.',
              'Tao-style Sol modal map uses 43 countries and lacks an unconditioned profile; it is not a paired prompting estimate.',
              'Main condition means have different coverage; inferential contrasts use matched cells.',
              'Expected-score and aggregated-argmax map common-country summaries use 91 countries.',
              'Provider-reported dollar costs are unavailable; dated list-price estimates are separate.',
            ]}
    (results/'publication_audit.json').write_text(json.dumps(report,indent=2))
    lines=['# Publication output inventory','',f"Validated {len(inventory)} CSV files and {len(figs['figures'])} canonical figures in three formats.",'',
           '| File | Rows | Columns | Missing entries |','|---|---:|---:|---:|']
    for r in inventory:lines.append(f"| `{r['file']}` | {r['rows']:,} | {len(r['columns'])} | {sum(r['missing_by_column'].values()):,} |")
    lines+=['','## Interpretation notes','']+[f'- {s}' for s in report['interpretation_notes']]
    Path('docs/PUBLICATION_OUTPUT_INVENTORY.md').write_text('\n'.join(lines)+'\n')
    print(f'Passed {len(checks)} integrity checks across {len(inventory)} CSV files.')

if __name__=='__main__':main()
