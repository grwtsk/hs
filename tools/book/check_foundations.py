"""Read-only editorial records. Structural validity is not human authentication.

No network, repairs, manuscript generation, model or interface runtime. A path
scan cannot prove that all interface behavior is absent. See validation/README.md.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys
from urllib.parse import urlsplit, unquote

LIMIT = 262144
FILES = {
    'work': ('planning/work.json', 'work_dependencies'),
    'edition': ('planning/edition.json', 'manuscript_commission'),
    'sources': ('research/source-evidence.json', 'source_evidence'),
    'instructions': ('contracts/author-instructions.json', 'author_instructions'),
    'proposals': ('decisions/agent-proposals.json', 'agent_proposals'),
    'human': ('decisions/human-dispositions.json', 'human_dispositions'),
    'dg': ('research/disagreements.yaml', 'disagreements'),
    'phase': ('contracts/phase.json', 'phase_scope'),
    'mismatch': ('research/technical-mismatches.json', 'technical_mismatches'),
}
FRONT = {'half-title', 'title', 'rights-and-edition', 'dedication', 'epigraph',
         'foreword', 'preface', 'readers-note', 'contents', 'lists'}
BACK = {'notes', 'bibliography', 'quotation-and-rights', 'glossary',
        'contract-appendix', 'source-appendix', 'disagreement-index',
        'acknowledgments', 'colophon', 'afterword', 'errata', 'index'}
DG_OWNERS = dict(zip((f'DG-{i:02}' for i in range(1, 13)),
                    (65, 8, 6, 7, 10, 9, 11, 7, 11, 10, 6, 6)))
DG_STATES = {'OPEN', 'PROPOSAL PREPARED', 'REOPENED', 'HUMAN ADOPTED FOR SCOPE',
             'HUMAN ACKNOWLEDGED / DISAGREEMENT RETAINED',
             'HUMAN DEFERRED / AFFECTED CAPABILITY EXCLUDED'}
ROLE_ISSUES = {6, 7, 8, 9, 10, 11, 65, 36, 38, 61}


class FoundationError(ValueError):
    """Fixed error code, never source/private text in a diagnostic."""


def need(condition, code):
    if not condition:
        raise FoundationError(code)


def fields(value, names, code='FIELDS'):
    need(type(value) is dict and set(value) == set(names.split()), code)


def text(value):
    need(type(value) is str and bool(value.strip()), 'TEXT')


def rows(value):
    need(type(value) is list, 'LIST')
    return value


def keys_by_id(items):
    result = {}
    for row in rows(items):
        need(type(row) is dict and type(row.get('id')) is str, 'RECORD_ID')
        text(row['id'])
        need(row['id'] not in result, 'DUPLICATE_ID')
        result[row['id']] = row
    return result


def sha(data):
    return hashlib.sha256(data).hexdigest()


def hash_value(value):
    need(type(value) is str and re.fullmatch('[0-9a-f]{64}', value) is not None, 'HASH')


def url(value):
    text(value)
    p = urlsplit(value)
    need(p.scheme == 'https' and bool(p.netloc) and p.username is None
         and p.password is None, 'URL')


def path(root, name):
    text(name)
    p = PurePosixPath(name)
    need(not p.is_absolute() and '..' not in p.parts and '\\' not in name,
         'PATH_ESCAPE')
    target = root
    for part in p.parts:
        target = target / part
        need(not target.is_symlink(), 'SYMLINK')
    need(target.resolve().is_relative_to(root.resolve()), 'PATH_ESCAPE')
    return target


def read(root, name):
    target = path(root, name)
    with target.open('rb') as stream:
        data = stream.read(LIMIT + 1)
    need(len(data) <= LIMIT, 'SIZE_LIMIT')
    return data


def unique(pairs):
    result = {}
    for k, v in pairs:
        need(k not in result, 'DUPLICATE_JSON_KEY')
        result[k] = v
    return result


def nonfinite(_):
    raise FoundationError('NONFINITE_JSON')


def load(root):
    result = {}
    for key, (name, kind) in FILES.items():
        value = json.loads(read(root, name), object_pairs_hook=unique,
                           parse_constant=nonfinite)
        need(type(value) is dict and type(value.get('schema_version')) is int
             and value['schema_version'] == 1 and value.get('kind') == kind,
             'SCHEMA_OR_KIND')
        result[key] = value
    return result


def refs(items, available, code='BROKEN_REFERENCE', nonempty=False):
    rows(items)
    need(len(items) == len(set(items)), 'DUPLICATE_REFERENCE')
    need(not nonempty or bool(items), code)
    need(all(x in available for x in items), code)


def issues(items, catalog, nonempty=False):
    rows(items)
    need(all(type(i) is int for i in items), 'ISSUE_TYPE')
    refs(items, catalog, 'UNKNOWN_ISSUE', nonempty)


def validate_work(d):
    w = d['work']
    fields(w, 'schema_version kind catalog owners index_source dependency_scope items')
    issues(w['catalog'], set(range(1, 72)) | {74, 75, 79, 80, 82}, True)
    catalog = set(w['catalog'])
    need(ROLE_ISSUES <= catalog and {1, 5, 16, 31, 32, 66} <= catalog,
         'MISSING_ISSUE')
    fields(w['owners'], ' '.join(str(i) for i in sorted(ROLE_ISSUES)))
    for owner in w['owners'].values():
        text(owner)
    url(w['index_source']); text(w['dependency_scope'])
    work = keys_by_id(w['items'])
    for r in work.values():
        fields(r, 'id issue kind parent_issue requires research_refs approval_gates state outputs')
        issues([r['issue']], catalog)
        need(r['kind'] in {'research','program','foundation','manuscript',
             'book_production','implementation','release','prototype_brief',
             'decision_packet','human_disposition'}, 'WORK_KIND')
        need(r['state'] in {'planned','in_review','pending_human','completed_source_custody'}, 'WORK_STATE')
        if r['state'] == 'completed_source_custody':
            need(r['issue'] in {2, 4}, 'FALSE_COMPLETION')
        if r['parent_issue'] is not None:
            issues([r['parent_issue']], catalog)
            need(r['parent_issue'] != r['issue'], 'SELF_PARENT')
        refs(r['requires'], work)
        issues(r['research_refs'], catalog)
        issues(r['approval_gates'], ROLE_ISSUES)
        need(bool(rows(r['outputs'])), 'OUTPUT_REQUIRED')
        for o in r['outputs']: text(o)
        need(r['id'] not in r['requires'], 'SELF_DEPENDENCY')
        for dep in r['requires']:
            need(work[dep]['issue'] != r['parent_issue'], 'CHILD_WAITS_FOR_PARENT')
            if r['kind'] == 'decision_packet':
                need(not (work[dep]['issue'] == r['issue'] and
                         work[dep]['kind'] == 'human_disposition'), 'PACKET_WAITS_FOR_APPROVAL')
        if r['kind'] == 'decision_packet':
            need(r['issue'] not in r['approval_gates'], 'PACKET_WAITS_FOR_APPROVAL')
        if 39 <= r['issue'] <= 60:
            need(r['kind'] == 'implementation', 'IMPLEMENTATION_RELABEL')
        if r['kind'] == 'implementation':
            need({36,38} <= set(r['approval_gates']), 'MISSING_IMPLEMENTATION_GATES')
        if r['issue'] == 62:
            need(r['kind'] == 'release' and {36,38,61} <= set(r['approval_gates']),
                 'MISSING_RELEASE_GATES')
    visiting, done = set(), set()
    def visit(k):
        need(k not in visiting, 'DEPENDENCY_CYCLE')
        if k in done: return
        visiting.add(k)
        for dep in work[k]['requires']: visit(dep)
        visiting.remove(k); done.add(k)
    for k in work: visit(k)
    for i in ROLE_ISSUES:
        prep, decide = f'I{i:03}.prepare', f'I{i:03}.decide'
        need(prep in work and decide in work and prep in work[decide]['requires'],
             'MISSING_PREPARATION')
    return catalog, w['owners']


def validate_sources(root, d):
    fields(d['sources'], 'schema_version kind items')
    sources = keys_by_id(d['sources']['items'])
    for s in sources.values():
        fields(s, 'id url version local_path sha256 reading_scope status public_copy')
        url(s['url']); text(s['version']); text(s['reading_scope'])
        need(s['status'] in {'read','reference_only_for_approval','unavailable'}, 'SOURCE_STATE')
        need(type(s['public_copy']) is bool, 'DISCLOSURE_TYPE')
        if s['local_path'] is not None:
            need(s['public_copy'] and s['status'] == 'read', 'PROTECTED_SOURCE_COPY')
            hash_value(s['sha256'])
            need(sha(read(root, s['local_path'])) == s['sha256'], 'SOURCE_DIGEST')
        else:
            need(s['sha256'] is None, 'UNVERIFIED_SOURCE_DIGEST')
    fields(d['instructions'], 'schema_version kind attribution items')
    text(d['instructions']['attribution'])
    for r in keys_by_id(d['instructions']['items']).values():
        fields(r, 'id source_refs supersedes summary')
        refs(r['source_refs'], sources, nonempty=True)
        for s in rows(r['supersedes']): text(s)
        text(r['summary'])
    return sources


def validate_decisions(root, d, sources, catalog, owners):
    fields(d['proposals'], 'schema_version kind items')
    proposals = keys_by_id(d['proposals']['items'])
    for p in proposals.values():
        fields(p, 'id origin owner_issue path sha256 source_refs scope state')
        need(p['origin'] == 'agent' and p['state'] == 'provisional', 'PROPOSAL_ROLE')
        issues([p['owner_issue']], ROLE_ISSUES)
        hash_value(p['sha256'])
        need(sha(read(root, p['path'])) == p['sha256'], 'PROPOSAL_DIGEST')
        refs(p['source_refs'], sources, nonempty=True)
        issues(p['scope'], catalog, True)
    fields(d['human'], 'schema_version kind items')
    humans = keys_by_id(d['human']['items'])
    for h in humans.values():
        fields(h, 'id evidence_origin recorded_by owner owner_issue proposal_id proposal_sha256 source_versions scope effect evidence_kind evidence_url conditions revocation retained_objections')
        need(h['evidence_origin'] == 'human' and h['recorded_by'] == 'agent', 'AGENT_IS_NOT_CONSENT')
        issues([h['owner_issue']], ROLE_ISSUES)
        need(h['owner'] == owners[str(h['owner_issue'])], 'HUMAN_OWNER')
        need(h['evidence_kind'] in {'task_channel_instruction','human_issue_instruction'}, 'OWNER_LOGIN_IS_NOT_CONSENT')
        url(h['evidence_url']); text(h['conditions']); text(h['revocation'])
        need(h['effect'] in {'adopt','retain','defer','reject'}, 'DISPOSITION_EFFECT')
        need(h['proposal_id'] in proposals, 'UNKNOWN_PROPOSAL')
        p = proposals[h['proposal_id']]
        need(h['owner_issue'] == p['owner_issue'], 'PROPOSAL_OWNER')
        need(h['proposal_sha256'] == p['sha256'], 'STALE_PROPOSAL_DECISION')
        expected = {}
        for sid in p['source_refs']:
            s = sources[sid]
            need(s['local_path'] is not None and s['status'] == 'read', 'UNPINNED_APPROVAL_SOURCE')
            expected[sid] = s['version'] + ':' + s['sha256']
        need(h['source_versions'] == expected, 'STALE_SOURCE_DECISION')
        issues(h['scope'], catalog, True)
        need(set(h['scope']) <= set(p['scope']), 'SCOPE_EXPANSION')
        for o in rows(h['retained_objections']): text(o)
        if h['effect'] == 'retain':
            need(bool(h['retained_objections']), 'SILENT_DISSENT_ERASURE')
    return humans


def validate_dg(root, d, catalog, sources, owners, humans):
    fields(d['dg'], 'schema_version kind format_note items')
    text(d['dg']['format_note'])
    dgs = keys_by_id(d['dg']['items'])
    need(set(dgs) == set(DG_OWNERS), 'ORPHAN_OR_MISSING_DG')
    apparatus = read(root, 'manuscript/back/disagreements.md').decode('utf-8')
    effects = {'HUMAN ADOPTED FOR SCOPE':'adopt',
               'HUMAN ACKNOWLEDGED / DISAGREEMENT RETAINED':'retain',
               'HUMAN DEFERRED / AFFECTED CAPABILITY EXCLUDED':'defer'}
    for r in dgs.values():
        fields(r, 'id kind question source_refs owner_issue owner affected_issues behavior_scope grounds countergrounds common_ground unknowns state disposition disposition_scope retained_objections reopen disclosure')
        need(r['kind'] in {'source_tension','agent_proposed_alternative','explicit_human_disagreement','unresolved_design_choice'}, 'DG_KIND')
        need(r['owner_issue'] == DG_OWNERS[r['id']] and r['owner'] == owners[str(r['owner_issue'])], 'DG_OWNER')
        refs(r['source_refs'], sources, nonempty=True)
        issues(r['affected_issues'], catalog, True)
        issues(r['behavior_scope'], set(range(39, 61)), True)
        need(r['disclosure'] == 'public_reference_only', 'DG_DISCLOSURE')
        for k in ('question','grounds','countergrounds','common_ground','unknowns','reopen'): text(r[k])
        need(r['state'] in DG_STATES, 'DG_STATE')
        if r['kind'] == 'explicit_human_disagreement':
            need(r['disposition'] in humans, 'HUMAN_DISAGREEMENT_EVIDENCE')
        need(f"## {r['id']} — {r['state']}" in apparatus, 'DG_MARKER_STATE')
        for o in rows(r['retained_objections']): text(o)
        if r['state'] in effects:
            need(r['disposition'] in humans, 'SILENT_DG_RESOLUTION')
            h = humans[r['disposition']]
            need(h['owner_issue'] == r['owner_issue'] and h['effect'] == effects[r['state']], 'DG_DISPOSITION')
            issues(r['disposition_scope'], catalog, True)
            need(set(r['disposition_scope']) <= set(h['scope'])
                 and set(r['disposition_scope']) <= set(r['affected_issues']), 'DG_SCOPE')
            need(r['retained_objections'] == h['retained_objections'], 'SILENT_DISSENT_ERASURE')
        else:
            need(r['disposition'] is None and r['disposition_scope'] == [], 'OPEN_DG_HAS_DECISION')
    return dgs


def validate_edition(root, d):
    e = d['edition']
    fields(e, 'schema_version kind front chapters back')
    need({r.get('id') for r in rows(e['front']) if type(r) is dict} == FRONT, 'FRONT_COMMISSION')
    need({r.get('id') for r in rows(e['back']) if type(r) is dict} == BACK, 'BACK_COMMISSION')
    need(len(e['front']) == len(FRONT) and len(e['back']) == len(BACK), 'DUPLICATE_MATTER')
    for part in ('front','back'):
        for r in e[part]:
            fields(r, 'id issue requirement state path')
            need(r['requirement'] in {'required','optional_if_approved'}, 'MATTER_REQUIREMENT')
            need(r['state'] in {'unwritten','provisional','working_apparatus'}, 'UNACCEPTED_COMPLETION')
            need(r['issue'] == 16 if part == 'front' else r['issue'] in {31,32}, 'MATTER_ISSUE')
            if r['state'] == 'unwritten': need(r['path'] is None, 'PLACEHOLDER_MANUSCRIPT')
            else:
                need(len(read(root, r['path']).strip()) > 0, 'EMPTY_MANUSCRIPT')
    need(len(rows(e['chapters'])) == 14, 'FOURTEEN_CHAPTERS')
    for n, c in enumerate(e['chapters'],1):
        fields(c, 'number issue title state path')
        need(type(c['number']) is int and c['number'] == n and type(c['issue']) is int
             and c['issue'] == n+16, 'CHAPTER_IDENTITY')
        text(c['title'])
        need(c['state'] in {'unwritten','provisional'}, 'UNACCEPTED_COMPLETION')
        if c['state'] == 'unwritten': need(c['path'] is None, 'PLACEHOLDER_MANUSCRIPT')
        else: need(bool(read(root, c['path']).strip()), 'EMPTY_MANUSCRIPT')


def validate_phase(root, d, catalog, humans, dgs):
    p = d['phase']
    fields(p, 'schema_version kind phase requested_scope gate_dispositions interface_artifacts')
    need(p['phase'] in {'manuscript','implementation','release'}, 'PHASE')
    fields(p['gate_dispositions'], '36 38 61')
    issues(p['requested_scope'], catalog)
    for gate, hid in p['gate_dispositions'].items():
        if hid is not None:
            need(hid in humans and humans[hid]['owner_issue'] == int(gate)
                 and humans[hid]['effect'] == 'adopt', 'INVALID_GATE')
    # This first foundation slice deliberately cannot admit implementation or
    # release. G1's complete-edition and G2's exact-artifact validators remain
    # work; accepting declarations alone would silently overstate those checks.
    need(p['phase'] == 'manuscript' and not p['requested_scope']
         and not rows(p['interface_artifacts'])
         and all(x is None for x in p['gate_dispositions'].values()),
         'PRODUCTION_ADMISSION_NOT_IMPLEMENTED')
    for f in root.rglob('*'):
        rel = f.relative_to(root)
        if '.git' in rel.parts or '__pycache__' in rel.parts: continue
        need(not f.is_symlink(), 'SYMLINK')
        if not f.is_file(): continue
        need(not (f.suffix.lower() in {'.js','.jsx','.ts','.tsx','.vue','.svelte','.html','.wasm','.onnx','.pt','.pth'}
                  or rel.parts[0] in {'app','apps','interface','runtime','models','node_modules'}),
             'UNAUTHORIZED_INTERFACE_SCOPE')
        if f.suffix.lower() == '.py':
            need(str(rel).startswith(('tools/book/','tests/')), 'UNDECLARED_EXECUTABLE')


def validate_links(root):
    # New manuscript/editorial docs only. Existing historical source captures
    # are not rewritten or treated as current instruction by this checker.
    names = ['AGENTS.md','CONTRIBUTING.md','RESUME.md','validation/README.md']
    for folder in ('manuscript','contracts','decisions'):
        names += [str(p.relative_to(root)) for p in (root/folder).rglob('*.md')]
    for name in names:
        data = read(root, name).decode('utf-8')
        data = re.sub(r'```.*?```', '', data, flags=re.S)
        for destination in re.findall(r'\]\(([^\s)]+)\)', data):
            if destination.startswith('https://'):
                url(destination); continue  # offline syntax only; not reachability
            need(':' not in destination and not destination.startswith('/'), 'LINK_SCHEME')
            target_name, _, anchor = unquote(destination).partition('#')
            target = (root/name).parent / target_name if target_name else root/name
            need(target.resolve().is_relative_to(root.resolve()), 'LINK_ESCAPE')
            relative = str(target.resolve().relative_to(root.resolve()))
            text_data = read(root, relative).decode('utf-8')
            if anchor:
                slugs = {re.sub(r'[^\w -]', '', h.lower()).replace(' ', '-')
                         for h in re.findall(r'^#+\s+(.+)$', text_data, re.M)}
                need(anchor in slugs, 'BROKEN_ANCHOR')


def check(root):
    d = load(root)
    catalog, owners = validate_work(d)
    sources = validate_sources(root, d)
    humans = validate_decisions(root, d, sources, catalog, owners)
    dgs = validate_dg(root, d, catalog, sources, owners, humans)
    validate_edition(root, d)
    validate_phase(root, d, catalog, humans, dgs)
    fields(d['mismatch'], 'schema_version kind items')
    for r in keys_by_id(d['mismatch']['items']).values():
        fields(r, 'id state evidence description')
        need(r['state'] in {'open','resolved_execution_gap','corrected'}, 'MISMATCH_STATE')
        url(r['evidence']); text(r['description'])
    validate_links(root)
    return {'work_nodes':len(d['work']['items']), 'chapters':14,
            'disagreements':len(dgs), 'human_dispositions':len(humans)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['check'])
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    try:
        result = check(args.root)
    except (OSError, ValueError, TypeError, KeyError, RecursionError, AttributeError) as exc:
        print(str(exc) if isinstance(exc, FoundationError) else 'FOUNDATION_READ_OR_FORMAT_ERROR', file=sys.stderr)
        return 1
    print('FOUNDATION_RECORDS_OK ' + ' '.join(f'{k}={v}' for k,v in result.items())
          + ' phase=manuscript authority=none production_admission=unimplemented')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
