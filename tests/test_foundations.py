"""Clearly synthetic record regressions; no manuscript or participant fixtures.

Only public schema shapes are copied. All prose, evidence bytes, locations and
human identities in temporary fixtures are synthetic. Positive human declarations
exercise structure, not authentication or actual consent.
"""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('hs_foundations', ROOT/'tools/book/check_foundations.py')
assert spec and spec.loader
f = importlib.util.module_from_spec(spec)
spec.loader.exec_module(f)


def put(root, name, value):
    p = root/name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(value, encoding='utf-8')


def synthetic(root):
    d = copy.deepcopy(f.load(ROOT))  # metadata shapes only, never source/prose bytes
    for owner in d['work']['owners']: d['work']['owners'][owner] = 'SYNTHETIC-HUMAN'
    d['work']['index_source'] = 'https://example.invalid/synthetic/issues'
    for r in d['work']['items']: r['outputs'] = ['SYNTHETIC planned output']
    for s in d['sources']['items']:
        s.update(url='https://example.invalid/synthetic/'+s['id'], version='SYNTHETIC-v1',
                 reading_scope='SYNTHETIC fixture only; not a real reading')
        if s['local_path'] is not None:
            put(root, s['local_path'], 'SYNTHETIC SOURCE: café, not an author instruction.\n')
            s['sha256'] = f.sha((root/s['local_path']).read_bytes())
    for r in d['instructions']['items']: r['summary'] = 'SYNTHETIC instruction summary'
    for c in d['edition']['chapters']: c['title'] = 'SYNTHETIC chapter '+str(c['number'])
    for r in d['dg']['items']:
        r['owner'] = 'SYNTHETIC-HUMAN'
        for k in ('question','grounds','countergrounds','common_ground','unknowns','reopen'):
            r[k] = 'SYNTHETIC '+k
    for p in d['proposals']['items']:
        put(root, p['path'], '# SYNTHETIC proposal\n\nThis is fixture text, not manuscript prose.\n')
        p['sha256'] = f.sha((root/p['path']).read_bytes())
    for r in d['mismatch']['items']:
        r['evidence'] = 'https://example.invalid/synthetic/run'
        r['description'] = 'SYNTHETIC mismatch'
    for n in ['AGENTS.md','CONTRIBUTING.md','RESUME.md','validation/README.md']:
        put(root, n, '# SYNTHETIC document\n')
    put(root, 'manuscript/back/disagreements.md', '# SYNTHETIC apparatus\n\n'+
        '\n\n'.join(f"## {r['id']} — {r['state']}\n\nSYNTHETIC tension." for r in d['dg']['items'])+'\n')
    return d


class FoundationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.d = synthetic(self.root)
        self.save()

    def save(self):
        for k, (p, _) in f.FILES.items():
            put(self.root, p, json.dumps(self.d[k], ensure_ascii=False, indent=2)+'\n')

    def check(self):
        self.save()
        return f.check(self.root)

    def fails(self, code):
        with self.assertRaisesRegex(f.FoundationError, '^'+code+'$'): self.check()

    def work(self, id):
        return next(x for x in self.d['work']['items'] if x['id'] == id)

    def declared_retention(self):
        p = self.d['proposals']['items'][0]
        p['source_refs'] = ['S-NAV']
        p['scope'] = [16,23,24,32]
        s = self.d['sources']['items'][0]
        h = dict(id='SYNTHETIC-DISPOSITION', evidence_origin='human', recorded_by='agent',
                 owner='SYNTHETIC-HUMAN', owner_issue=6, proposal_id=p['id'],
                 proposal_sha256=p['sha256'], source_versions={'S-NAV':s['version']+':'+s['sha256']},
                 scope=p['scope'][:], effect='retain', evidence_kind='task_channel_instruction',
                 evidence_url='https://example.invalid/synthetic/human-instruction/1',
                 conditions='SYNTHETIC fixture, no real consent.', revocation='SYNTHETIC revocation.',
                 retained_objections=['SYNTHETIC remaining objection'])
        self.d['human']['items'] = [h]
        dg = self.d['dg']['items'][2]
        dg['state'] = 'HUMAN ACKNOWLEDGED / DISAGREEMENT RETAINED'
        dg['disposition'] = h['id']
        dg['disposition_scope'] = h['scope'][:]
        dg['retained_objections'] = h['retained_objections'][:]
        pth = self.root/'manuscript/back/disagreements.md'
        pth.write_text(pth.read_text().replace('## DG-03 — OPEN','## DG-03 — '+dg['state']))
        return h, dg, p

    def test_actual_public_record_integrity(self):
        self.assertEqual(f.check(ROOT)['chapters'], 14)

    def test_open_disagreement_allows_provisional_writing(self):
        self.assertEqual(self.check()['disagreements'], 12)

    def test_declared_retained_disagreement_is_structurally_valid(self):
        self.declared_retention()
        self.assertEqual(self.check()['human_dispositions'], 1)

    def test_retention_can_cover_one_passage_scope_not_all_work(self):
        h, dg, _ = self.declared_retention()
        h['scope'] = [16]
        dg['disposition_scope'] = [16]
        self.check()

    def test_research_references_are_not_blocking_edges(self):
        self.work('I005')['research_refs'] = [1,5,66]
        self.check()

    def test_preparation_does_not_require_approval(self):
        self.assertEqual(self.work('I006.prepare')['requires'], [])
        self.check()

    def test_packet_waiting_for_own_approval_rejected(self):
        self.work('I006.prepare')['requires'] = ['I006.decide']
        self.fails('PACKET_WAITS_FOR_APPROVAL')

    def test_packet_with_own_gate_rejected(self):
        self.work('I006.prepare')['approval_gates'] = [6]
        self.fails('PACKET_WAITS_FOR_APPROVAL')

    def test_child_waiting_for_parent_rejected(self):
        self.work('I005')['requires'] = ['I001']
        self.fails('CHILD_WAITS_FOR_PARENT')

    def test_dependency_cycle_rejected(self):
        self.work('I012')['requires'] = ['I013']
        self.work('I013')['requires'] = ['I012']
        self.fails('DEPENDENCY_CYCLE')

    def test_self_dependency_rejected(self):
        self.work('I005')['requires'] = ['I005']
        self.fails('SELF_DEPENDENCY')

    def test_unknown_dependency_rejected(self):
        self.work('I005')['requires'] = ['SYNTHETIC-MISSING']
        self.fails('BROKEN_REFERENCE')

    def test_unknown_issue_rejected(self):
        self.work('I005')['research_refs'] = [999999]
        self.fails('UNKNOWN_ISSUE')

    def test_boolean_issue_rejected(self):
        self.work('I005')['issue'] = True
        self.fails('ISSUE_TYPE')

    def test_duplicate_work_rejected(self):
        self.d['work']['items'].append(copy.deepcopy(self.work('I005')))
        self.fails('DUPLICATE_ID')

    def test_missing_schema_field_rejected(self):
        del self.work('I005')['outputs']
        self.fails('FIELDS')

    def test_extra_approval_field_rejected(self):
        self.d['instructions']['items'][0]['approved'] = True
        self.fails('FIELDS')

    def test_agent_origin_is_not_human_consent(self):
        h, _, _ = self.declared_retention(); h['evidence_origin'] = 'agent'
        self.fails('AGENT_IS_NOT_CONSENT')

    def test_login_alone_is_not_consent(self):
        h, _, _ = self.declared_retention(); h['evidence_kind'] = 'owner_login'
        self.fails('OWNER_LOGIN_IS_NOT_CONSENT')

    def test_missing_human_evidence_rejected(self):
        h, _, _ = self.declared_retention(); del h['evidence_url']
        self.fails('FIELDS')

    def test_wrong_human_owner_rejected(self):
        h, _, _ = self.declared_retention(); h['owner'] = 'OTHER-SYNTHETIC-HUMAN'
        self.fails('HUMAN_OWNER')

    def test_stale_proposal_decision_rejected(self):
        h, _, p = self.declared_retention()
        put(self.root, p['path'], 'SYNTHETIC revised proposal\n')
        p['sha256'] = f.sha((self.root/p['path']).read_bytes())
        self.fails('STALE_PROPOSAL_DECISION')

    def test_changed_proposal_without_rebinding_rejected(self):
        p = self.d['proposals']['items'][0]
        put(self.root, p['path'], 'SYNTHETIC changed text\n')
        self.fails('PROPOSAL_DIGEST')

    def test_stale_source_decision_rejected(self):
        self.declared_retention()
        self.d['sources']['items'][0]['version'] = 'SYNTHETIC-v2'
        self.fails('STALE_SOURCE_DECISION')

    def test_unpinned_remote_source_cannot_bind_approval(self):
        _, _, p = self.declared_retention(); p['source_refs'].append('S-DG66')
        self.fails('UNPINNED_APPROVAL_SOURCE')

    def test_scope_expansion_rejected(self):
        h, _, _ = self.declared_retention(); h['scope'].append(52)
        self.fails('SCOPE_EXPANSION')

    def test_disposition_scope_does_not_cover_dg(self):
        h, _, _ = self.declared_retention(); h['scope'].remove(23)
        self.fails('DG_SCOPE')

    def test_retained_dissent_cannot_be_emptied(self):
        h, _, _ = self.declared_retention(); h['retained_objections'] = []
        self.fails('SILENT_DISSENT_ERASURE')

    def test_dg_dissent_must_match_disposition(self):
        _, dg, _ = self.declared_retention(); dg['retained_objections'] = []
        self.fails('SILENT_DISSENT_ERASURE')

    def test_silent_dg_resolution_rejected(self):
        _, dg, _ = self.declared_retention(); self.d['human']['items'] = []
        self.fails('SILENT_DG_RESOLUTION')

    def test_rejection_is_not_adoption(self):
        h, _, _ = self.declared_retention(); h['effect'] = 'reject'
        self.fails('DG_DISPOSITION')

    def test_orphan_dg_rejected(self):
        self.d['dg']['items'].pop()
        self.fails('ORPHAN_OR_MISSING_DG')

    def test_changed_dg_owner_rejected(self):
        self.d['dg']['items'][0]['owner_issue'] = 6
        self.fails('DG_OWNER')

    def test_changed_visible_dg_marker_rejected(self):
        p=self.root/'manuscript/back/disagreements.md'; p.write_text(p.read_text().replace('DG-01','DG-99'))
        self.fails('DG_MARKER_STATE')

    def test_protected_source_cannot_be_copied(self):
        self.d['sources']['items'][0]['public_copy'] = False
        self.fails('PROTECTED_SOURCE_COPY')

    def test_source_digest_rejected(self):
        s=self.d['sources']['items'][0]; put(self.root,s['local_path'],'SYNTHETIC corrupted source')
        self.fails('SOURCE_DIGEST')

    def test_broken_source_reference_rejected(self):
        self.d['instructions']['items'][0]['source_refs']=['SYNTHETIC-MISSING']
        self.fails('BROKEN_REFERENCE')

    def test_path_escape_rejected(self):
        self.d['sources']['items'][0]['local_path']='../synthetic.txt'
        self.fails('PATH_ESCAPE')

    def test_symlink_rejected(self):
        (self.root/'alias.md').symlink_to(self.root/'AGENTS.md')
        self.fails('SYMLINK')

    def test_broken_local_link_rejected(self):
        put(self.root,'AGENTS.md','[SYNTHETIC link](missing.md)\n')
        self.save()
        with self.assertRaises(OSError): f.check(self.root)

    def test_broken_local_anchor_rejected(self):
        put(self.root,'AGENTS.md','[SYNTHETIC link](RESUME.md#missing)\n')
        self.fails('BROKEN_ANCHOR')

    def test_unsafe_link_scheme_rejected(self):
        put(self.root,'AGENTS.md','[SYNTHETIC link](javascript:void)\n')
        self.fails('LINK_SCHEME')

    def test_duplicate_json_keys_rejected(self):
        with self.assertRaisesRegex(f.FoundationError,'DUPLICATE_JSON_KEY'):
            json.loads('{"synthetic":1,"synthetic":2}',object_pairs_hook=f.unique)

    def test_nonfinite_json_rejected(self):
        for token in ('NaN','Infinity','-Infinity'):
            with self.subTest(token=token), self.assertRaisesRegex(f.FoundationError,'NONFINITE_JSON'):
                json.loads('{"synthetic":'+token+'}',parse_constant=f.nonfinite)

    def test_boolean_schema_rejected(self):
        self.d['phase']['schema_version']=True; self.save()
        with self.assertRaisesRegex(f.FoundationError,'SCHEMA_OR_KIND'): f.check(self.root)

    def test_size_bound_rejected(self):
        put(self.root,'synthetic.txt','x'*(f.LIMIT+1))
        with self.assertRaisesRegex(f.FoundationError,'SIZE_LIMIT'): f.read(self.root,'synthetic.txt')

    def test_interface_javascript_rejected(self):
        put(self.root,'research/synthetic.js','// SYNTHETIC inert fixture\n')
        self.fails('UNAUTHORIZED_INTERFACE_SCOPE')

    def test_interface_path_rejected(self):
        put(self.root,'runtime/synthetic.txt','SYNTHETIC inert fixture\n')
        self.fails('UNAUTHORIZED_INTERFACE_SCOPE')

    def test_undeclared_python_rejected(self):
        put(self.root,'synthetic.py','# SYNTHETIC inert fixture\n')
        self.fails('UNDECLARED_EXECUTABLE')

    def test_unapproved_implementation_phase_rejected(self):
        self.d['phase']['phase']='implementation'
        self.fails('PRODUCTION_ADMISSION_NOT_IMPLEMENTED')

    def test_unapproved_release_phase_rejected(self):
        self.d['phase']['phase']='release'
        self.fails('PRODUCTION_ADMISSION_NOT_IMPLEMENTED')

    def test_undeclared_gate_rejected(self):
        self.d['phase']['gate_dispositions']['36']='SYNTHETIC-MISSING'
        self.fails('INVALID_GATE')

    def test_implementation_relabel_rejected(self):
        self.work('I052')['kind']='research'
        self.fails('IMPLEMENTATION_RELABEL')

    def test_implementation_gate_removal_rejected(self):
        self.work('I052')['approval_gates']=[36]
        self.fails('MISSING_IMPLEMENTATION_GATES')

    def test_release_gate_removal_rejected(self):
        self.work('I062')['approval_gates']=[36,38]
        self.fails('MISSING_RELEASE_GATES')

    def test_human_quarrel_cannot_be_invented(self):
        self.d['dg']['items'][0]['kind']='explicit_human_disagreement'
        self.fails('HUMAN_DISAGREEMENT_EVIDENCE')

    def test_fourteenth_chapter_cannot_disappear(self):
        self.d['edition']['chapters'].pop()
        self.fails('FOURTEEN_CHAPTERS')

    def test_false_chapter_completion_rejected(self):
        self.d['edition']['chapters'][0]['state']='complete'
        self.fails('UNACCEPTED_COMPLETION')

    def test_front_matter_cannot_disappear(self):
        self.d['edition']['front'].pop()
        self.fails('FRONT_COMMISSION')

    def test_back_matter_cannot_disappear(self):
        self.d['edition']['back'].pop()
        self.fails('BACK_COMMISSION')

    def test_unapproved_optional_omission_rejected(self):
        self.d['edition']['front'][3]['state']='omitted'
        self.fails('UNACCEPTED_COMPLETION')

    def test_empty_provisional_manuscript_rejected(self):
        self.d['edition']['chapters'][0].update(state='provisional',path='manuscript/chapters/synthetic.md')
        put(self.root,'manuscript/chapters/synthetic.md',' \n')
        self.fails('EMPTY_MANUSCRIPT')

    def test_mismatch_is_not_a_vote(self):
        self.d['mismatch']['items'][0]['state']='approved_by_vote'
        self.fails('MISMATCH_STATE')

    def test_checker_is_read_only(self):
        self.save()
        def snapshot(): return {str(p.relative_to(self.root)):f.sha(p.read_bytes()) for p in self.root.rglob('*') if p.is_file()}
        before=snapshot(); f.check(self.root); self.assertEqual(before,snapshot())

    def test_cli_success_and_fixed_failure(self):
        command=[sys.executable,'-B',str(ROOT/'tools/book/check_foundations.py'),'check','--root',str(self.root)]
        result=subprocess.run(command,capture_output=True,text=True,timeout=10,check=False)
        self.assertEqual(result.returncode,0,result.stderr); self.assertIn('authority=none',result.stdout)
        self.d['human']['items']=[{'id':'SYNTHETIC invented approval'}]; self.save()
        result=subprocess.run(command,capture_output=True,text=True,timeout=10,check=False)
        self.assertEqual(result.returncode,1); self.assertEqual(result.stderr.strip(),'FIELDS')


if __name__ == '__main__':
    unittest.main()
