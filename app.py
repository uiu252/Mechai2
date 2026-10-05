"""Merch AI — human in the loop Halloween assortment copilot."""
from pathlib import Path
from datetime import datetime
import hashlib
import html
import json
import os
import pandas as pd
import streamlit as st
from data_loader import load_products, fingerprint, source_warnings, DEFAULT_WORKBOOK, WorkbookError
from schemas import ROLES, CATEGORIES, PLACEMENTS, Product, Review, Change, MerchantDecision
from rules import validate_assortment, apply_changes
from agents import (demo_analyses, live_analyses, offline_synthesis, live_synthesis, MODEL,
                    money, pct)
from workflow import finalize, summary_markdown, placements_csv, record_json
from scenarios import SCENARIOS, load_scenario
from errors import explain_error

st.set_page_config(page_title='Merch AI · Halloween assortment', page_icon='🎃', layout='wide', initial_sidebar_state='expanded')
st.markdown('''<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');
html,body,[class*="css"],.stApp {font-family:'DM Sans',sans-serif;}
h1,h2,h3 {font-family:'Manrope',sans-serif;letter-spacing:-.045em;}
.block-container {padding:4.2rem 2.5rem 3rem;max-width:1550px;}
h1 {font-size:2.7rem!important;font-weight:800!important;}
h2 {font-size:1.6rem!important;}
h3 {font-size:1.1rem!important;}
[data-testid="stSidebar"] {border-right:1px solid #DCDDD5;}
[data-testid="stMetric"] {background:#FFFFFF;border:1px solid #E1E2DA;border-radius:12px;padding:18px 22px;}
[data-testid="stMetricLabel"] {color:#687369;text-transform:uppercase;letter-spacing:.07em;font-size:11px;}
[data-testid="stMetricLabel"] p {font-size:11px!important;white-space:normal!important;}
[data-testid="stMetricDelta"] svg {display:none;}
[data-testid="stMetricDelta"] > div {font-size:12px;white-space:normal;}
.stDeployButton {display:none;}
[data-testid="stMetricValue"] {font-family:'Manrope',sans-serif;font-size:2rem;font-weight:700;}
.eyebrow {font-size:11px;font-weight:700;letter-spacing:.17em;text-transform:uppercase;color:#A34D1A;margin-bottom:10px;}
.lede {color:#647068;font-size:16px;margin-top:-10px;margin-bottom:25px;}
.brand {font-family:'Manrope',sans-serif;font-size:25px;font-weight:800;letter-spacing:-1px;margin:0 0 4px;}
.brand em {font-style:normal;color:#C25F28;}
.sidebar-label {font-size:10px;letter-spacing:.16em;color:#7A827A;margin:24px 0 10px;}
.rule {font-size:12px;display:inline-block;padding:7px 11px;background:#E8EFE7;color:#31533D;border-radius:6px;margin:0 6px 6px 0;}
.rule.fail {background:#FBE9E2;color:#9E3624;}
.aisle {display:flex;gap:5px;margin:12px 0 9px;height:44px;}
.slot {flex:1;min-width:0;border-radius:5px;background:#DEE3D9;}
.slot.giant {background:#485F50}.slot.inflatable{background:#AFBE96}.slot.decor{background:#D78A55}
.legend {font-size:12px;color:#626D63;display:flex;gap:18px;flex-wrap:wrap;margin-bottom:4px;}
.legend b {display:inline-block;width:8px;height:8px;border-radius:2px;margin-right:6px;}
.stepnote {font-size:12px;color:#758074;margin:10px 0;}
div.stButton > button {border-radius:8px;font-weight:600;}
[data-testid="stTabs"] button {font-weight:600;}
.finding-number {color:#B26438;font-weight:700;font-size:11px;letter-spacing:.1em;}
.footer {font-size:11px;color:#838A82;border-top:1px solid #DDDFD5;padding-top:15px;margin-top:35px;}
@media(max-width:768px){.block-container{padding:4rem 1rem 2rem}h1{font-size:2rem!important}}
</style>''', unsafe_allow_html=True)

STAGES = ('Assortment', 'Specialist review', 'Executive synthesis', 'Merchant decision')
s = st.session_state

def clear_downstream():
    for key in ('analyses', 'analysis_fingerprint', 'analysis_source', 'analysis_provenance', 'reviews',
                'synthesis', 'synthesis_source', 'synthesis_review_fingerprint', 'final_products', 'final_record'):
        s.pop(key, None)
    s['review_epoch'] = s.get('review_epoch', 0) + 1

def set_products(products):
    s['products'] = products
    s['editor_version'] = s.get('editor_version', 0) + 1
    clear_downstream()

def go(stage): s['stage'] = stage
def queue_job(job):
    if not s.get('busy'):
        s['job'] = job
        s['busy'] = True

def reviews_fingerprint():
    return hashlib.sha256(json.dumps({k:v.model_dump() for k,v in sorted(s.get('reviews', {}).items())}, sort_keys=True).encode()).hexdigest()

def notify(message): s['notice'] = message

def escaped(value):
    # Streamlit treats paired dollar signs as LaTeX. Currency is plain text here.
    return str(value).replace('$', r'\$')

def prose(value): st.markdown(escaped(value))

def editor_frame(products):
    return pd.DataFrame([{'Product': p.item, 'Placement': p.placement,
        'Category': p.category, 'Required facings': p.required_facings,
        'Source': 'Historical actuals' if p.source_type == 'current' else 'Supplier estimate',
        'Retail price': p.retail_price,
        'Historical GM': p.gross_margin_dollars if p.source_type == 'current' else None,
        'Potential GM': p.gross_margin_dollars if p.source_type == 'new_candidate' else None,
        'Full-price sell-through': p.full_price_sell_through,
        'Stars': p.star_rating, 'Reviews': p.reviews,
        'Mandatory buy': p.mandatory_purchase_quantity} for p in products])

def edit_placements(products, widget_key, height=490):
    frame = editor_frame(products)
    edited = st.data_editor(frame, key=widget_key, hide_index=True, use_container_width=True,
        height=height, num_rows='fixed', disabled=[c for c in frame.columns if c != 'Placement'],
        column_config={
            'Product': st.column_config.TextColumn(width='large'),
            'Placement': st.column_config.SelectboxColumn(options=PLACEMENTS, required=True, width='medium'),
            'Retail price': st.column_config.NumberColumn(format='$%.2f'),
            'Historical GM': st.column_config.NumberColumn(format='$%.0f'),
            'Potential GM': st.column_config.NumberColumn(format='$%.0f'),
            'Full-price sell-through': st.column_config.NumberColumn(format='%.2f', help='Fraction from 0 to 1; 0.85 means 85%. Missing is not zero.'),
        })
    return [p.model_copy(update={'placement': edited.iloc[i]['Placement']}) for i, p in enumerate(products)]

def show_validation(products, compact=False):
    v = validate_assortment(products)
    cols = st.columns(4)
    cols[0].metric('In-store facings', f'{v.total_facings} / 16', 'Capacity met' if v.facings_valid else f'{abs(16-v.total_facings)} {"needed" if v.total_facings<16 else "over capacity"}', delta_color='off' if v.facings_valid else 'inverse')
    cols[1].metric('Online-only items', f'{v.online_count} / 4', 'Within limit' if v.online_valid else 'Limit exceeded', delta_color='off' if v.online_valid else 'inverse')
    cols[2].metric('Required categories', f'{3-len(v.missing_categories)} / 3', 'Represented in store', delta_color='off')
    cols[3].metric('Assortment checks', 'PASS' if v.valid else 'NEEDS EDIT', f'{sum(p.placement == "In Store" for p in products)} in-store products', delta_color='off')
    badges = ''.join(f'<span class="rule {"" if c in v.categories else "fail"}">{"✓" if c in v.categories else "×"} {html.escape(c)}</span>' for c in CATEGORIES)
    badges += f'<span class="rule {"" if v.placement_valid else "fail"}">{"✓" if v.placement_valid else "×"} Exclusive placements</span>'
    st.markdown(badges, unsafe_allow_html=True)
    if not compact:
        slots = []
        for p in products:
            if p.placement != 'In Store': continue
            css = {'Giants & Animatronics':'giant','Inflatables':'inflatable','Decor & Accessories':'decor'}.get(p.category, '')
            slots.extend(f'<div class="slot {css}" title="{html.escape(p.item, quote=True)}"></div>' for _ in range(p.required_facings))
        slots.extend('<div class="slot"></div>' for _ in range(max(0,16-v.total_facings)))
        st.markdown('<div class="aisle">'+''.join(slots)+'</div><div class="legend"><span><b style="background:#485F50"></b>Giants & animatronics</span><span><b style="background:#AFBE96"></b>Inflatables</span><span><b style="background:#D78A55"></b>Decor & accessories</span><span>One block = one facing</span></div>', unsafe_allow_html=True)
    for error in v.errors: st.error(error)
    return v

def display_changes(changes):
    if not changes: st.info('No placement changes proposed. Keep the current assortment.'); return
    st.dataframe(pd.DataFrame([{'Product': c.product, 'From': c.from_placement,
        'To': c.to_placement, 'Reason': c.reason} for c in changes]), hide_index=True, use_container_width=True)

def pretty_metric(field, value):
    if value == 'Not available': return value
    if field in ('gross_margin_dollars','retail_price','unit_cost','historical_gm_per_facing','total_sales'):
        return f'${float(value):,.2f}'
    if field in ('gross_margin_rate','full_price_sell_through'): return f'{float(value):.2%}'
    return value

if 'products' not in s:
    try:
        s['products'] = load_products()
        s['source_name'] = DEFAULT_WORKBOOK.name
        s['editor_version'] = 0
        s['review_epoch'] = 0
    except WorkbookError as exc:
        st.error(str(exc)); st.stop()

with st.sidebar:
    st.markdown('<div class="brand">merch<em> ai</em><span style="font-size:14px;margin-left:8px">◈</span></div>', unsafe_allow_html=True)
    st.caption('THE HUMAN-LED ASSORTMENT STUDIO')
    st.markdown('<div class="sidebar-label">SEASON / HALLOWEEN</div>', unsafe_allow_html=True)
    st.radio('Workspace', STAGES, key='stage', label_visibility='collapsed')
    st.divider()
    st.markdown('**Analysis mode**')
    mode = st.radio('Choose analysis mode', ['Demo Mode', 'Live AI'], key='mode', label_visibility='collapsed')
    api_key = None
    model = MODEL
    if mode == 'Live AI':
        model = st.text_input('Model', value=MODEL)
        st.caption('One model, three independent perspectives and a separate synthesis call.')
    else:
        st.caption('No API needed. Baseline uses cached prepared analysis; edited assortments use clearly labeled rule-based analysis.')
    st.divider()
    with st.expander('Data & demo scenarios'):
        st.caption(f'Source: {s["source_name"]}')
        upload = st.file_uploader('Load Student Data workbook', type=['xlsx'])
        if st.button('Load uploaded workbook', disabled=upload is None or s.get('busy',False), use_container_width=True):
            try:
                products = load_products(upload.getvalue())
                set_products(products); s['source_name'] = upload.name
                notify('Workbook loaded. Reviews and recommendations reset for the new data.'); st.rerun()
            except WorkbookError as exc: st.error(str(exc))
        scenario = st.selectbox('Rehearsal assortment', SCENARIOS)
        if st.button('Load scenario', use_container_width=True, disabled=s.get('busy',False)):
            try:
                set_products(load_scenario(s['products'], scenario))
                notify(f'{scenario} loaded. Previous review results cleared.'); st.rerun()
            except ValueError as exc: st.error(str(exc))
        st.caption('Loading a workbook or scenario resets the current review workflow.')
    st.markdown('<div class="sidebar-label">DECISION RIGHTS</div>', unsafe_allow_html=True)
    st.caption('AI challenges. Specialists review. The merchant decides. Code enforces the rules.')
    if mode == 'Live AI':
        st.divider()
        api_key = st.text_input('OpenAI API key', type='password', help='Optional if OPENAI_API_KEY is configured. Kept only in this browser session.')
        if not api_key and not os.environ.get('OPENAI_API_KEY'): st.info('No key configured. Demo Mode is ready.')

products = s['products']
if s.get('analyses') and s.get('analysis_fingerprint') != fingerprint(products): clear_downstream()
st.markdown('<div class="eyebrow">Halloween line review / Decision workspace</div>', unsafe_allow_html=True)
heading = {'Assortment':'Make room for the right mix.', 'Specialist review':'Three lenses. Human judgment.',
           'Executive synthesis':'Bring the perspectives together.', 'Merchant decision':'The final call is yours.'}[s['stage']]
st.title(heading)
st.markdown('<div class="lede">Merch AI · Human in the loop assortment copilot</div>', unsafe_allow_html=True)
if s.get('notice'): st.success(s.pop('notice'))
if s.get('job_error'):
    st.warning(s['job_error'])
    if st.button('Dismiss warning'): s.pop('job_error'); st.rerun()
st.caption(f'{len(products)} products · {sum(p.source_type == "current" for p in products)} historical actuals · {sum(p.source_type == "new_candidate" for p in products)} supplier candidates · {s["source_name"]}')

if s['stage'] == 'Assortment':
    validation = show_validation(products)
    left, right = st.columns([3,2])
    left.subheader('Build the aisle')
    right.button('Continue to specialist review →', on_click=go, args=('Specialist review',), use_container_width=True)
    st.caption('Edit Placement, then save. Historical GM and potential GM are separate measures; neither is a forecast. Blank metric cells mean Not available.')
    with st.form('workspace_editor'):
        updated = edit_placements(products, f'workspace_{s["editor_version"]}')
        if st.form_submit_button('Save placements & validate', type='primary'):
            if fingerprint(updated) != fingerprint(products):
                set_products(updated)
                notify('Placements saved and checked. Run new perspectives for this assortment.')
            else: notify('Placements checked. No changes to the assortment.')
            st.rerun()
    with st.expander('Product evidence & source notes'):
        selected = st.selectbox('Inspect product', [p.item for p in products])
        p = next(p for p in products if p.item == selected)
        a,b,c = st.columns(3)
        a.metric('Retail price', money(p.retail_price))
        b.metric('Historical realized GM' if p.source_type == 'current' else 'Supplier potential GM', money(p.gross_margin_dollars))
        c.metric('Realized GM rate' if p.source_type == 'current' else 'Estimated unit margin rate', pct(p.gross_margin_rate))
        st.caption(f'Source: Student Data, row {p.source_row}. Placement: {p.placement}. Required facings: {p.required_facings}.')
        st.write({'Full-price sell-through':pct(p.full_price_sell_through), 'Star rating':p.star_rating if p.star_rating is not None else 'Not available', 'Reviews':p.reviews if p.reviews is not None else 'Not available', 'Mandatory purchase':p.mandatory_purchase_quantity if p.mandatory_purchase_quantity is not None else 'Not available', 'Licensed': 'Not available' if p.licensed is None else ('Yes' if p.licensed else 'No')})
        if p.vendor_says: prose('**Supplier claim:** ' + p.vendor_says)
        if p.merchant_notes: prose('**Merchant note:** ' + p.merchant_notes)
        st.json(p.model_dump(), expanded=False)
    warnings = source_warnings(products)
    if warnings:
        with st.expander(f'Source quality notes · {len(warnings)}'):
            for warning in warnings: st.warning(escaped(warning))

elif s['stage'] == 'Specialist review':
    v = validate_assortment(products)
    st.subheader('Independent perspectives')
    st.write('Review the same assortment through financial, customer, and operational lenses. Save one human decision for each perspective.')
    if not v.valid: st.warning('You can inspect analyses, but synthesis and finalization stay blocked until every assortment rule passes.')
    st.button('Run three perspectives' if mode == 'Live AI' else 'Load demo perspectives',
        type='primary', on_click=queue_job, args=('analyses',), disabled=s.get('busy',False))
    if s.get('job') == 'analyses':
        s.pop('job')
        try:
            with st.spinner('Reviewing product evidence through three independent perspectives… Live requests can take a few minutes; please keep this page open.'):
                if mode == 'Live AI':
                    results = live_analyses(products, api_key, model)
                    label, provenance = f'Live AI · {model}', 'Three independent model analyses. AI selects workbook references; Python fills their source values. Review the reasoning before approving.'
                else: results, label, provenance = demo_analyses(products)
                clear_downstream()
                s.update(analyses=results, analysis_fingerprint=fingerprint(products), analysis_source=label,
                         analysis_provenance=provenance, reviews={})
                s.pop('job_error', None)
        except Exception as exc:
            # Do not echo SDK exception payloads, credentials or request headers.
            s['job_error'] = 'Analysis did not complete. ' + explain_error(exc) + ' Existing results, if any, are unchanged.'
        finally: s['busy'] = False
        st.rerun()
    if s.get('analyses'):
        st.info(f'{s["analysis_source"]} · {s["analysis_provenance"]}')
        count = len(s.get('reviews',{}))
        st.progress(count / 3, text=f'{count} of 3 human reviews saved')
        tabs = st.tabs(ROLES)
        for index, (tab, role) in enumerate(zip(tabs, ROLES)):
            with tab:
                a = s['analyses'][role]
                st.subheader(a.verdict.replace('_',' ').capitalize())
                for i,f in enumerate(a.findings,1):
                    st.markdown(f'<div class="finding-number">FINDING {i:02}</div>', unsafe_allow_html=True)
                    prose(f.claim)
                    with st.expander('View workbook evidence', expanded=False):
                        rows = []
                        for e in f.evidence:
                            product = next(p for p in products if p.item == e.product)
                            rows.append({'Product':e.product, 'Metric':e.field.replace('_',' '),
                                'Value':pretty_metric(e.field,e.value), 'Row':product.source_row,
                                'Basis':'Historical actuals' if product.source_type == 'current' else 'Supplier estimate'})
                        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
                st.warning(escaped('Primary risk: ' + a.primary_risk))
                st.markdown('**Proposed assortment change**')
                display_changes(a.recommended_changes)
                st.divider()
                old = s.get('reviews',{}).get(role)
                if old: st.success(f'Saved human review: {old.decision}')
                epoch = s['review_epoch']
                with st.form(f'review_{index}_{epoch}'):
                    st.markdown('**Your specialist decision**')
                    decision = st.radio('Human decision', ['Agree','Modify','Disagree'], index=['Agree','Modify','Disagree'].index(old.decision) if old else 0, horizontal=True, key=f'decision_{index}_{epoch}')
                    comment = st.text_area('Reviewer comment', value=old.comment if old else '',
                        help='Required for Modify or Disagree. Cite product evidence. Saved comments are passed to synthesis verbatim.', key=f'comment_{index}_{epoch}')
                    with st.expander('Optional explicit placement changes'):
                        st.caption('For Modify or Disagree, edit any placements below. These are requests for synthesis, not changes to the working assortment. Free-text comments alone never silently move products in Demo Mode.')
                        initial = apply_changes(products, old.requested_changes) if old and old.requested_changes else products
                        requested = st.data_editor(pd.DataFrame([{'Product':p.item,'Requested placement':p.placement} for p in initial]),
                            hide_index=True, use_container_width=True, height=230, disabled=['Product'],
                            column_config={'Requested placement':st.column_config.SelectboxColumn(options=PLACEMENTS,required=True)}, key=f'requests_{index}_{epoch}')
                    if st.form_submit_button('Save human review', type='primary'):
                        try:
                            if decision in ('Modify', 'Disagree') and not comment.strip():
                                raise ValueError('Add a Reviewer comment explaining your decision, then click Save human review again. Mention the products and the evidence behind your change.')
                            changes = [Change(product=p.item, from_placement=p.placement,
                                to_placement=requested.iloc[i]['Requested placement'], reason=comment.strip() or 'Reviewer request')
                                for i,p in enumerate(products) if requested.iloc[i]['Requested placement'] != p.placement]
                            review = Review(role=role, decision=decision, comment=comment.strip(), requested_changes=changes)
                            s.setdefault('reviews',{})[role] = review
                            for k in ('synthesis','final_products','final_record'): s.pop(k,None)
                            notify(f'{role} review saved. Synthesis will use your decision and comment.'); st.rerun()
                        except ValueError as exc: st.error(str(exc))
        st.button('Continue to executive synthesis →', on_click=go, args=('Executive synthesis',), disabled=count != 3)
    else: st.info('Run or load the perspectives to begin specialist review.')

elif s['stage'] == 'Executive synthesis':
    st.subheader('A recommendation shaped by the team')
    v = show_validation(products, compact=True)
    ready = bool(s.get('analyses')) and len(s.get('reviews',{})) == 3 and v.valid
    if not ready: st.info('Complete all three human reviews and pass every assortment rule to unlock synthesis.')
    st.button('Synthesize recommendation', type='primary', on_click=queue_job, args=('synthesis',), disabled=not ready or s.get('busy',False))
    if s.get('job') == 'synthesis':
        s.pop('job')
        try:
            with st.spinner('Combining specialist evidence and human decisions… Live requests can take a few minutes; please keep this page open.'):
                reviews = list(s['reviews'].values())
                if mode == 'Live AI':
                    synthesis = live_synthesis(products, s['analyses'], reviews, api_key, model)
                    source = f'Live AI synthesis · {model}'
                else:
                    synthesis = offline_synthesis(products, s['analyses'], reviews)
                    source = 'Rule-based demo synthesis'
                s['synthesis'] = synthesis
                s['synthesis_source'] = source
                s['synthesis_review_fingerprint'] = reviews_fingerprint()
                s['final_products'] = apply_changes(products, synthesis.recommended_changes, require_valid=True)
                s['final_editor_version'] = s.get('final_editor_version',0)+1
                s.pop('final_record',None)
                s.pop('job_error',None)
        except Exception as exc:
            s['job_error'] = 'Synthesis did not complete. ' + explain_error(exc) + ' No new recommendation was applied. Demo Mode remains available.'
        finally: s['busy'] = False
        st.rerun()
    if s.get('synthesis'):
        syn = s['synthesis']
        st.info(s['synthesis_source'])
        prose(syn.executive_rationale)
        a,b = st.columns(2)
        with a:
            st.subheader('Agreements')
            for x in syn.agreements: prose('✓ ' + x)
        with b:
            st.subheader('Conflicts & tradeoffs')
            for x in syn.conflicts: prose('• ' + x)
            if not syn.conflicts: st.caption('No explicit reviewer disagreement recorded.')
        st.subheader('How human judgment changed the result')
        for r in syn.reviewer_responses:
            with st.container(border=True):
                st.markdown(f'**{r.role} · {r.decision}**')
                if r.comment: prose('Reviewer: ' + r.comment)
                prose(r.disposition)
        st.subheader('Recommended placements')
        display_changes(syn.recommended_changes)
        with st.expander('Unresolved risks & confidence', expanded=True):
            for risk in syn.risks: prose('• ' + risk)
            st.caption(escaped(syn.confidence_note))
        st.button('Continue to merchant decision →', type='primary', on_click=go, args=('Merchant decision',))

elif s['stage'] == 'Merchant decision':
    if not s.get('synthesis'):
        st.info('Complete specialist review and synthesis before making the final decision.')
        st.button('Go to specialist review', on_click=go, args=('Specialist review',))
    elif s.get('synthesis_review_fingerprint') != reviews_fingerprint():
        st.warning('Human reviews changed. Run synthesis again before finalization.')
    else:
        syn = s['synthesis']
        proposed = apply_changes(products,syn.recommended_changes,require_valid=True)
        final_products = s.get('final_products',proposed)
        st.subheader('Review the final assortment')
        v = show_validation(final_products)
        st.caption('The table begins with the synthesized recommendation. Save any final placement edits, then choose Accept, Modify or Override. Every final decision must pass the same rules.')
        with st.form('final_editor'):
            edited = edit_placements(final_products,f'final_{s.get("final_editor_version",0)}',height=350)
            if st.form_submit_button('Save final placements & validate'):
                s['final_products'] = edited
                s.pop('final_record',None)
                s['final_editor_version'] = s.get('final_editor_version',0)+1
                notify('Final placements saved and revalidated.'); st.rerun()
        with st.form('merchant_decision'):
            rationale = st.text_area('Merchant rationale', help='Required for Modify or Override. Accept requires placements to match synthesis exactly.')
            c1,c2,c3 = st.columns(3)
            accept = c1.form_submit_button('Accept recommendation',type='primary',disabled=not v.valid,use_container_width=True)
            modify = c2.form_submit_button('Finalize modified assortment',disabled=not v.valid,use_container_width=True)
            override = c3.form_submit_button('Override recommendation',disabled=not v.valid,use_container_width=True)
            if accept or modify or override:
                try:
                    decision = MerchantDecision(decision='Accept' if accept else 'Modify' if modify else 'Override', rationale=rationale.strip())
                    s['final_record'] = finalize(products, final_products, s['analyses'], list(s['reviews'].values()),
                        syn, decision, s['analysis_fingerprint'], s['analysis_source'], s['synthesis_source'])
                    notify('Decision finalized. All assortment rules pass. Export the summary below.'); st.rerun()
                except ValueError as exc: st.error(str(exc))
        if s.get('final_record'):
            record = s['final_record']
            st.success(f'Finalized · {record["merchant_decision"]["decision"]} · {record["validation"]["total_facings"]}/16 facings · {record["validation"]["online_count"]}/4 online-only items')
            st.subheader('Your presentation-ready decision')
            text = summary_markdown(record)
            c1,c2,c3 = st.columns(3)
            c1.download_button('Download decision summary',text,'Merch_AI_Decision.md','text/markdown',use_container_width=True)
            c2.download_button('Download final placements',placements_csv(record),'Merch_AI_Placements.csv','text/csv',use_container_width=True)
            c3.download_button('Download complete audit record',record_json(record),'Merch_AI_Audit.json','application/json',use_container_width=True)
            with st.expander('Copy summary into your presentation',expanded=True): st.code(text,language=None)

st.markdown('<div class="footer">MERCH AI / MVP &nbsp; · &nbsp; Workbook-grounded evidence &nbsp; · &nbsp; Human review required &nbsp; · &nbsp; Deterministic final validation<br>Session changes are kept in this browser session. Download the final audit record to retain your decision.</div>',unsafe_allow_html=True)
