"""Author the data path while preserving existing lesson IDs and progress."""
import json, textwrap
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
original = json.loads((ROOT/'app/curriculum.json').read_text(encoding='utf-8'))[:4]
new = []
def course(id, title, description, stage, icon, color):
    c = dict(id=id,title=title,subtitle=description,description=description,level=stage,
             stage=stage,icon=icon,color=color,land=title,time='3–5 hours',lessons=[])
    new.append(c)
    return c
def q(c, slug, title, scenario, concept, task, signature, solution, tests, sample, hint, packages=None, project=False):
    code = textwrap.dedent(solution).strip()+'\n'
    checks = textwrap.dedent(tests).strip()
    assert checks.count('assert ') + checks.count('raise AssertionError') >= 3, title
    imports = ''.join(f'import {p} as {"pd" if p=="pandas" else "np"}\n' for p in (packages or []))
    starter = imports+'\n'+signature+':\n    # Implement the contract described in Your quest.\n    pass\n\n'+sample+'\n'
    c['lessons'].append(dict(id=c['id']+'-'+slug,title=title,summary=scenario,theory=scenario+'\n\n'+concept+'\n\nWork from the function contract: inspect the sample, implement the transformation, then check boundary cases. Return data rather than printing inside the function; the sample print is only for inspection.',example=sample,task=task,starter=starter,hint=hint,solution=code+'\n'+sample+'\n',tests=checks,input='',minutes=45 if project else 25,xp=150 if project else 75,packages=packages or [],project=project))

c=course('data-toolkit','Python for Messy Data','Turn strings, files, timestamps, and nested records into trustworthy inputs.','Data foundations','🧰','#bde58c')
q(c,'money','Money without float surprises','A finance export mixes rupee signs, commas, whitespace, and missing amounts.',
  'Decimal parses base-10 text exactly. Financial rounding is a business rule: use ROUND_HALF_UP here, then convert rupees to integer paise. Treat an empty value as missing; reject malformed numbers rather than silently turning them into zero.',
  'Implement to_paise(value): accept a string or None. Strip whitespace, ₹, and commas. Return None for None or blank text. Round valid finite nonnegative amounts to 2 decimal places using ROUND_HALF_UP and return integer paise. Raise ValueError for negatives, NaN, infinity, or invalid text.',
  'def to_paise(value)',
  '''from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
def to_paise(value):
    if value is None or not value.strip():
        return None
    try:
        amount = Decimal(value.strip().replace('₹', '').replace(',', ''))
        if not amount.is_finite() or amount < 0:
            raise ValueError('Invalid amount')
        return int(amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP) * 100)
    except InvalidOperation as exc:
        raise ValueError('Invalid amount') from exc''',
  '''assert to_paise(' ₹1,200.505 ') == 120051, 'Use decimal half-up rounding.'
assert to_paise('0') == 0 and to_paise('') is None and to_paise(None) is None, 'Keep missing distinct from zero.'
for bad in ['-1','NaN','Infinity','oops']:
    try: to_paise(bad)
    except ValueError: pass
    else: raise AssertionError('Reject invalid or negative amounts: '+bad)''',
  "print(to_paise('₹1,200.505'))  # 120051",'Use Decimal on cleaned text, check is_finite(), quantize, then multiply by 100.')
q(c,'emails','Normalize customer identities','A CRM contains duplicate emails with inconsistent spacing and capitalization.',
  'Normalize only according to a stated business policy. Lowercasing is the policy in this exercise; provider-specific tricks such as removing dots can incorrectly combine distinct customers. A set supports membership checks while a list preserves first-seen order.',
  'Implement unique_emails(values). Ignore None and blank strings. Strip outer whitespace, lowercase, and retain only strings with exactly one @ and nonempty text on both sides. Return unique normalized strings in first-seen order. Do not modify values. This is a simple ingestion check, not complete email validation.',
  'def unique_emails(values)',
  '''def unique_emails(values):
    seen, result = set(), []
    for value in values:
        if value is None: continue
        email = value.strip().lower()
        if email.count('@') != 1 or not all(email.split('@')): continue
        if email not in seen:
            seen.add(email)
            result.append(email)
    return result''',
  '''source = [' A@X.COM ', None, 'a@x.com', 'b@y.io', 'bad', '@x', 'x@@y', '']
before = source[:]
assert unique_emails(source) == ['a@x.com','b@y.io'], 'Normalize, validate, deduplicate, and preserve order.'
assert source == before, 'Do not mutate input.'
assert unique_emails([]) == [] and unique_emails([' X@Y ', 'z@q', 'x@y']) == ['x@y','z@q'], 'Handle empty and repeated identities.' ''',
  "print(unique_emails([' A@X.COM ', 'a@x.com', None]))  # ['a@x.com']",'Track normalized values in a set, appending only new valid identities.')
q(c,'batches','Batch a one-pass source','Your source is a generator too large to materialize into a list.',
  'A generator yields items on demand. Batch using a small buffer so memory depends on the batch size, not the source size. Validate the requested size even if the source is empty. The final batch may contain fewer items.',
  'Implement batches(items, size) as a generator yielding lists with at most size items, preserving order. Consume a one-pass iterable once. Yield no batches for empty input. Raise ValueError when size <= 0.',
  'def batches(items, size)',
  '''def batches(items, size):
    if size <= 0: raise ValueError('size must be positive')
    batch = []
    for item in items:
        batch.append(item)
        if len(batch) == size:
            yield batch
            batch = []
    if batch: yield batch''',
  '''assert list(batches(iter(range(5)),2)) == [[0,1],[2,3],[4]], 'Keep the partial final batch.'
assert list(batches([],3)) == [] and list(batches([1],5)) == [[1]], 'Handle empty and short sources.'
try: list(batches([],0))
except ValueError: pass
else: raise AssertionError('Reject zero batch size even for an empty source.')
import itertools
assert list(itertools.islice(batches(itertools.count(),2),2)) == [[0,1],[2,3]], 'Do not materialize the whole iterable.' ''',
  'print(list(batches(iter(range(5)), 2)))  # [[0, 1], [2, 3], [4]]','Yield when a buffer reaches size, replace it with a new list, then yield a nonempty remainder.')
q(c,'latest','Keep the latest customer update','A daily dump contains several versions of the same customer, out of arrival order.',
  'Choose a deterministic survivor before joining datasets. Here updated_at is an ISO UTC string in a single fixed format, so lexical order equals time order. Retain the last occurrence when timestamps tie; do not rely on arbitrary set ordering.',
  'Implement latest_records(rows). Each row has id and updated_at (YYYY-MM-DDTHH:MM:SSZ). Keep the greatest timestamp per id, choosing the later input row on ties. Return copied rows sorted by id. IDs are strings. Do not mutate the input.',
  'def latest_records(rows)',
  '''def latest_records(rows):
    latest = {}
    for row in rows:
        if row['id'] not in latest or row['updated_at'] >= latest[row['id']]['updated_at']:
            latest[row['id']] = dict(row)
    return [latest[key] for key in sorted(latest)]''',
  '''rows=[{'id':'a','updated_at':'2026-01-02T00:00:00Z','v':2},{'id':'a','updated_at':'2026-01-01T00:00:00Z','v':1},{'id':'b','updated_at':'2026-01-01T00:00:00Z','v':3}]
assert [r['v'] for r in latest_records(rows)] == [2,3], 'Use event timestamp, not arrival order.'
assert latest_records([]) == [], 'Empty source should return an empty list.'
tie=latest_records([rows[0],dict(rows[0],v=9)])
assert tie[0]['v']==9, 'Choose the later input on timestamp ties.'
result=latest_records(rows); result[0]['v']=100
assert rows[0]['v']==2, 'Return independent row dictionaries.' ''',
  "print(latest_records([{'id':'a','updated_at':'2026-01-01T00:00:00Z'}]))",'Use a dictionary keyed by id and update when the new timestamp is >= the saved timestamp.')
q(c,'csv','CSV is not split on commas','A vendor sends customer names containing commas inside quotes.',
  'Use csv.DictReader rather than splitting lines manually. A parser understands quoting and embedded delimiters. Perform type conversion after parsing and attach the CSV record number to errors so a colleague can locate the bad record.',
  'Implement read_orders(text). Parse CSV headers order_id,customer,amount. Return (valid, rejected). valid contains dictionaries with integer order_id, stripped customer, and float amount. Reject rows with invalid integer/float values, blank customers, nonfinite amounts, or negative amounts. rejected is a list of CSV record numbers (header is 1, first data record is 2). Preserve input order; assume no multiline fields.',
  'def read_orders(text)',
  '''import csv, io, math
def read_orders(text):
    valid, rejected = [], []
    for number, row in enumerate(csv.DictReader(io.StringIO(text)),2):
        try:
            order_id, amount = int(row['order_id']), float(row['amount'])
            customer = row['customer'].strip()
            if not customer or not math.isfinite(amount) or amount < 0: raise ValueError('invalid row')
            valid.append(dict(order_id=order_id,customer=customer,amount=amount))
        except (ValueError, TypeError, KeyError, AttributeError):
            rejected.append(number)
    return valid, rejected''',
  r'''valid,bad=read_orders('order_id,customer,amount\n1,"Doe, Ada",20.5\nx,Bob,3\n2, ,9\n3,Cat,-1\n4,Dan,NaN\n')
assert valid==[{'order_id':1,'customer':'Doe, Ada','amount':20.5}], 'Honor CSV quoting and convert numeric types.'
assert bad==[3,4,5,6], 'Report bad CSV record numbers.'
assert read_orders('order_id,customer,amount\n') == ([],[]), 'Header-only files are valid empty inputs.' ''',
  r"print(read_orders('order_id,customer,amount\n1,Ada,20.5\n'))", 'Parse with csv.DictReader over io.StringIO; catch only expected conversion errors.')
q(c,'json','Flatten nested API orders','An API returns orders with nested customer and line-item objects.',
  'Flattening changes the grain of data: an order becomes one row per line item. Missing nested data needs an explicit policy. Empty line-item lists produce no rows. Retain the order key so downstream metrics can distinguish orders from items.',
  'Implement flatten_orders(orders). Each order has id, optional customer (None or a dict with optional email), and optional items (a list of sku/qty dicts). Return one dict per item with order_id, email (None if missing), sku, qty. Preserve order and do not mutate the input.',
  'def flatten_orders(orders)',
  '''def flatten_orders(orders):
    return [dict(order_id=o['id'],email=(o.get('customer') or {}).get('email'),sku=i['sku'],qty=i['qty'])
            for o in orders for i in o.get('items', [])]''',
  '''source=[{'id':1,'customer':{'email':'a@x'},'items':[{'sku':'A','qty':2},{'sku':'B','qty':1}]},{'id':2,'items':[]},{'id':3,'customer':None,'items':[{'sku':'C','qty':1}]}]
assert len(flatten_orders(source))==3, 'The output grain is one row per item.'
assert flatten_orders(source)[-1]=={'order_id':3,'email':None,'sku':'C','qty':1}, 'Handle missing customer information.'
assert flatten_orders([])==[] and source[0]['items'][0]=={'sku':'A','qty':2}, 'Handle empty input without mutation.' ''',
  "print(flatten_orders([{'id':1,'items':[{'sku':'A','qty':2}]}]))",'Use a nested loop and (order.get("customer") or {}) for nullable customers.')
q(c,'utc','A business day crosses midnight','An event recorded at 00:30 in India belongs to the previous UTC date.',
  'A naive datetime has no offset and cannot identify an instant unambiguously. Parse offset-aware ISO text, convert to UTC, and only then take the date. Do not simply slice the first ten characters of the original timestamp.',
  'Implement utc_day(timestamp). Accept ISO-8601 text with Z or an explicit offset. Return the UTC date as YYYY-MM-DD. Raise ValueError when the timestamp is naive or invalid.',
  'def utc_day(timestamp)',
  '''from datetime import datetime, timezone
def utc_day(timestamp):
    dt = datetime.fromisoformat(timestamp.replace('Z','+00:00'))
    if dt.tzinfo is None: raise ValueError('Offset required')
    return dt.astimezone(timezone.utc).date().isoformat()''',
  '''assert utc_day('2026-01-02T00:30:00+05:30')=='2026-01-01', 'Convert to UTC before selecting a date.'
assert utc_day('2026-01-01T23:30:00-02:00')=='2026-01-02' and utc_day('2026-01-01T00:00:00Z')=='2026-01-01', 'Handle negative offsets and Z.'
try: utc_day('2026-01-01T12:00:00')
except ValueError: pass
else: raise AssertionError('Reject naive timestamps.')''',
  "print(utc_day('2026-01-02T00:30:00+05:30'))  # 2026-01-01",'Use datetime.fromisoformat and astimezone(timezone.utc).')
q(c,'profile','Project: profile an incoming batch','An analyst needs an honest summary before approving a new dataset.',
  'A data profile describes missingness, uniqueness, and ranges without rewriting the source. A missing value is not zero. Make the empty-batch behavior explicit so monitoring does not divide by zero or report invented extrema.',
  'Implement profile_rows(rows). Rows contain id and amount (number or None). Return a dict with rows, missing_amounts, duplicate_ids (total rows minus distinct ids), and amount_min/amount_max over nonmissing amounts, or None when no values exist. Zero is a valid amount. Do not mutate rows.',
  'def profile_rows(rows)',
  '''def profile_rows(rows):
    values=[r['amount'] for r in rows if r['amount'] is not None]
    return dict(rows=len(rows),missing_amounts=len(rows)-len(values),duplicate_ids=len(rows)-len({r['id'] for r in rows}),amount_min=min(values) if values else None,amount_max=max(values) if values else None)''',
  '''rows=[{'id':1,'amount':0},{'id':1,'amount':None},{'id':2,'amount':9}]
assert profile_rows(rows)=={'rows':3,'missing_amounts':1,'duplicate_ids':1,'amount_min':0,'amount_max':9}, 'Separate zero, missing, and duplicated keys.'
assert profile_rows([])=={'rows':0,'missing_amounts':0,'duplicate_ids':0,'amount_min':None,'amount_max':None}, 'Do not invent bounds for an empty batch.'
assert profile_rows([{'id':1,'amount':None}])['amount_max'] is None and rows[0]['amount']==0, 'Handle all-missing values without mutation.' ''',
  "print(profile_rows([{'id':1,'amount':0},{'id':1,'amount':None}]))",'Collect nonmissing amounts, count distinct ids, and guard empty min/max.',project=True)

c=course('numpy-lab','NumPy for Data Work','Compute with arrays, broadcasting, missing values, and numerical edge cases.','Junior analyst','🔢','#84dcd4')
q(c,'mask','Filter sensor readings','A sensor sometimes emits negative values or NaN instead of a valid measurement.',
  'NumPy boolean masks select many elements at once. Combine conditions with & and put each comparison in parentheses. np.isfinite excludes NaN and both infinities. Return a new array so callers can safely retain the source.',
  'Implement valid_readings(values). Convert a 1-D numeric sequence to a float ndarray and return only finite, nonnegative values in their original order. Do not modify input.',
  'def valid_readings(values)',
  '''import numpy as np
def valid_readings(values):
    a=np.asarray(values,dtype=float)
    return a[np.isfinite(a) & (a >= 0)]''',
  '''a=np.array([1.,-2.,np.nan,np.inf,0.]); before=a.copy()
assert isinstance(valid_readings(a),np.ndarray) and np.array_equal(valid_readings(a),[1.,0.]), 'Use a finite, nonnegative mask.'
assert valid_readings([]).size==0, 'Empty sequences should produce empty arrays.'
assert np.array_equal(a,before,equal_nan=True), 'Do not mutate the sensor array.' ''',
  'print(valid_readings([2, -1, float("nan"), 0]))  # [2. 0.]','Combine np.isfinite(a) with a >= 0.',packages=['numpy'])
q(c,'divide','Ratios with a zero denominator','A daily conversion report includes campaigns with no visitors.',
  'An undefined ratio should remain missing rather than becoming zero. np.divide accepts out and where, allowing valid divisions without warnings. Allocate a float output because integer arrays cannot represent NaN.',
  'Implement safe_ratio(numerator, denominator) for same-shaped numeric arrays. Return a float ndarray of elementwise ratios. Return NaN wherever denominator is zero. Do not mutate either input; assume other values are finite.',
  'def safe_ratio(numerator, denominator)',
  '''import numpy as np
def safe_ratio(numerator, denominator):
    a,b=np.asarray(numerator,dtype=float),np.asarray(denominator,dtype=float)
    return np.divide(a,b,out=np.full(a.shape,np.nan),where=b!=0)''',
  '''result=safe_ratio([2,0,3],[4,0,0])
assert np.isclose(result[0],.5) and np.isnan(result[1:]).all(), 'Use NaN for undefined ratios.'
assert np.array_equal(safe_ratio([-2,4],[2,-2]),[-1,-2]), 'Preserve signs.'
assert safe_ratio([],[]).size==0, 'Handle empty arrays.' ''',
  'print(safe_ratio([2, 0], [4, 0]))  # [0.5 nan]','Initialize a NaN float output and use np.divide(..., where=denominator != 0).',packages=['numpy'])
q(c,'scale','Standardize feature columns','A model needs each numerical feature centered and scaled independently.',
  'For a 2-D matrix with rows as observations, axis=0 reduces over rows and produces one statistic per column. Broadcasting then applies those statistics back to every row. Constant columns have zero variance and should become zero instead of causing division errors.',
  'Implement standardize(matrix). For a nonempty 2-D float matrix, return columnwise z-scores using population standard deviation (ddof=0). Constant columns must be zero. Do not mutate the matrix.',
  'def standardize(matrix)',
  '''import numpy as np
def standardize(matrix):
    a=np.asarray(matrix,dtype=float)
    std=a.std(axis=0)
    return (a-a.mean(axis=0))/np.where(std==0,1,std)''',
  '''a=np.array([[1.,9.],[3.,9.],[5.,9.]]); before=a.copy(); result=standardize(a)
assert np.allclose(result[:,0],[-1.2247448714,0,1.2247448714]), 'Use columnwise population standard deviation.'
assert np.array_equal(result[:,1],[0,0,0]) and np.array_equal(a,before), 'Handle constant columns without mutation.'
assert np.allclose(standardize([[7,8]]),[[0,0]]), 'A single observation has zero z-scores.' ''',
  'print(standardize([[1, 9], [3, 9], [5, 9]]))','Compute means/stds with axis=0 and substitute 1 for zero standard deviations.',packages=['numpy'])
q(c,'weighted','A weighted price is not an average of prices','Stores sell different numbers of units at different prices.',
  'A weighted mean is sum(value * weight) / sum(weight). Averaging store averages ignores exposure. Validate weights: negative unit counts are invalid here, while all-zero weights mean no defined average.',
  'Implement weighted_price(prices, units). Inputs are equal-length 1-D finite numeric sequences. Return their weighted mean as a float, or None when total units is zero (including empty input). Raise ValueError for any negative units.',
  'def weighted_price(prices, units)',
  '''import numpy as np
def weighted_price(prices, units):
    p,u=np.asarray(prices,dtype=float),np.asarray(units,dtype=float)
    if (u<0).any(): raise ValueError('negative weight')
    return float((p*u).sum()/u.sum()) if u.sum() else None''',
  '''assert np.isclose(weighted_price([10,20],[9,1]),11), 'Weight by units, not by stores.'
assert weighted_price([],[]) is None and weighted_price([5],[0]) is None, 'No exposure means no defined average.'
try: weighted_price([3,4],[2,-1])
except ValueError: pass
else: raise AssertionError('Reject negative unit counts.')''',
  'print(weighted_price([10,20], [9,1]))  # 11.0','Use elementwise multiplication and sum; guard zero and negative total exposure.',packages=['numpy'])
q(c,'winsor','Clip extreme values reproducibly','A preprocessing step limits extreme values using thresholds learned elsewhere.',
  'Winsorization replaces extremes with boundary values; it does not delete rows. Keeping thresholds as arguments separates fitting from transformation and prevents computing new thresholds on evaluation data. np.clip performs the operation without a Python loop.',
  'Implement clip_values(values, low, high). Return a new float array with values clipped to inclusive bounds; preserve NaN. Raise ValueError if low > high. Do not mutate the input.',
  'def clip_values(values, low, high)',
  '''import numpy as np
def clip_values(values, low, high):
    if low>high: raise ValueError('reversed bounds')
    return np.clip(np.asarray(values,dtype=float),low,high)''',
  '''a=np.array([-9.,2.,99.,np.nan]); result=clip_values(a,0,10)
assert np.allclose(result[:3],[0,2,10]) and np.isnan(result[3]), 'Clip without dropping missing values.'
assert a[0]==-9 and clip_values([],0,1).size==0, 'Return a fresh array and support empty input.'
try: clip_values([1],10,0)
except ValueError: pass
else: raise AssertionError('Reject reversed bounds.')''',
  'print(clip_values([-9,2,99], 0,10))  # [0. 2. 10.]','Validate the bounds, then call np.clip without an out argument.',packages=['numpy'])
q(c,'impute','Fill missing features by column','One numerical feature is entirely missing in a new batch.',
  'Imputation needs an all-missing policy. Here each column uses its observed mean; columns with no observed values use zero. This exercise profiles one batch; in a modeling workflow learn imputation values from training data only.',
  'Implement impute_columns(matrix) for a nonempty 2-D matrix containing finite numbers or NaN. Replace NaN with the column mean, or 0 for all-missing columns. Return a new float array. Do not change observed values or mutate input.',
  'def impute_columns(matrix)',
  '''import numpy as np
def impute_columns(matrix):
    a=np.array(matrix,dtype=float,copy=True)
    counts=np.sum(~np.isnan(a),axis=0)
    means=np.divide(np.nansum(a,axis=0),counts,out=np.zeros(a.shape[1]),where=counts!=0)
    return np.where(np.isnan(a),means,a)''',
  '''a=np.array([[1.,np.nan,np.nan],[3.,5.,np.nan]]); before=a.copy()
assert np.allclose(impute_columns(a),[[1,5,0],[3,5,0]]), 'Use observed column means with zero fallback.'
assert np.array_equal(a,before,equal_nan=True), 'Do not mutate source data.'
assert np.array_equal(impute_columns([[np.nan]]),[[0]]), 'Handle an entirely missing matrix.' ''',
  'print(impute_columns([[1,float("nan")],[3,5]]))','Divide nansum by nonmissing counts using a guarded output, then use np.where.',packages=['numpy'])
q(c,'distances','Match observations to centroids','A segmentation job must compare every customer vector to every centroid.',
  'Add singleton dimensions to broadcast observations (n,1,d) against centroids (1,k,d). Sum squared differences across the feature axis, then take a square root. This produces an (n,k) distance matrix; very large n*k*d requires batching in production.',
  'Implement distances(points, centers). Inputs are 2-D arrays with the same number of features. Return Euclidean distances with shape (number of points, number of centers). Support zero-row arrays with known feature dimension. Do not mutate inputs.',
  'def distances(points, centers)',
  '''import numpy as np
def distances(points, centers):
    p,c=np.asarray(points,dtype=float),np.asarray(centers,dtype=float)
    return np.sqrt(((p[:,None,:]-c[None,:,:])**2).sum(axis=2))''',
  '''assert np.allclose(distances([[0,0],[3,4]],[[0,0],[0,4]]),[[0,4],[5,3]]), 'Reduce across features, not observations.'
assert distances(np.empty((0,2)),np.zeros((3,2))).shape==(0,3), 'Keep dimensions for no observations.'
assert distances(np.ones((2,2)),np.empty((0,2))).shape==(2,0), 'Support no centroids.' ''',
  'print(distances([[0,0],[3,4]], [[0,0]]))  # [[0.], [5.]]','Subtract points[:,None,:] and centers[None,:,:], square, sum axis=2, sqrt.',packages=['numpy'])
q(c,'kpi','Project: a weekly metrics matrix','A product dashboard receives rows of visits and conversions for several days.',
  'A report should distinguish missing exposure from genuine zero conversion. Aggregate numerator and denominator before dividing; taking an unweighted mean of daily rates gives low-traffic days too much influence. A compact NumPy pipeline can return trustworthy summary values.',
  'Implement summarize_traffic(matrix). Each row is [visits, conversions], with nonnegative counts and conversions <= visits. Return a dict with visits (int sum), conversions (int sum), rate (total conversions / total visits or None), and active_days (rows with visits > 0). Raise ValueError for negative counts or conversions exceeding visits. Accept an empty array of shape (0,2).',
  'def summarize_traffic(matrix)',
  '''import numpy as np
def summarize_traffic(matrix):
    a=np.asarray(matrix)
    if (a<0).any() or (a[:,1]>a[:,0]).any(): raise ValueError('invalid counts')
    visits,conversions=int(a[:,0].sum()),int(a[:,1].sum())
    return dict(visits=visits,conversions=conversions,rate=conversions/visits if visits else None,active_days=int((a[:,0]>0).sum()))''',
  '''assert summarize_traffic([[100,10],[10,5],[0,0]])=={'visits':110,'conversions':15,'rate':15/110,'active_days':2}, 'Aggregate counts before calculating the rate.'
assert summarize_traffic(np.empty((0,2)))=={'visits':0,'conversions':0,'rate':None,'active_days':0}, 'Handle empty traffic.'
for bad in [[[-1,0]],[[2,3]]]:
    try: summarize_traffic(bad)
    except ValueError: pass
    else: raise AssertionError('Validate traffic count constraints.')''',
  'print(summarize_traffic([[100,10],[10,5],[0,0]]))','Validate the two columns, sum each, and compute a ratio of sums.',packages=['numpy'],project=True)

c=course('pandas-workbench','pandas: Clean & Transform','Clean real tables and make joins, aggregations, and time series behave correctly.','Junior analyst','🐼','#b5c5ff')
q(c,'types','Coerce a dirty amount column','A spreadsheet export stores amounts as strings and includes blanks and bad tokens.',
  'pd.to_numeric(errors="coerce") converts invalid tokens to missing values. Clean string formatting first, then convert. Return a copy instead of changing a DataFrame supplied by a caller. A missing numeric value should not automatically become zero.',
  'Implement clean_amounts(df). Return a copy with amount converted to numeric after removing commas and surrounding whitespace. Invalid strings and None become NaN. Keep all rows, other columns, and the original index.',
  'def clean_amounts(df)',
  '''import pandas as pd
def clean_amounts(df):
    out=df.copy()
    out['amount']=pd.to_numeric(out['amount'].astype('string').str.replace(',','',regex=False).str.strip(),errors='coerce')
    return out''',
  '''df=pd.DataFrame({'amount':[' 1,200 ','bad',None,'0'],'id':[1,2,3,4]},index=[8,7,6,5]); result=clean_amounts(df)
assert result.loc[8,'amount']==1200 and result.loc[5,'amount']==0 and result['amount'].isna().sum()==2, 'Coerce invalid tokens but retain zero.'
assert result.index.equals(df.index) and result['id'].equals(df['id']), 'Preserve rows, index, and other columns.'
assert df.loc[8,'amount']==' 1,200 ' and clean_amounts(df.iloc[:0]).empty, 'Do not mutate input; handle an empty frame.' ''',
  "print(clean_amounts(pd.DataFrame({'amount':['1,200','bad','0']})))",'Copy the frame, use string operations, then pd.to_numeric(errors="coerce").',packages=['pandas'])
q(c,'missing','Audit missingness before filling','A team asks which fields are too incomplete to use.',
  'isna().mean() measures missing fractions per column because booleans act as zero/one. Missingness is defined over observed rows; for an empty table use an explicit zero policy here. Keep column order so the output matches the source schema.',
  'Implement missing_report(df). Return a DataFrame indexed by the original column names with columns missing_count (integer) and missing_fraction (0–1). For zero rows, use 0.0 fractions. Do not mutate df.',
  'def missing_report(df)',
  '''import pandas as pd
def missing_report(df):
    counts=df.isna().sum()
    return pd.DataFrame({'missing_count':counts,'missing_fraction':counts/len(df) if len(df) else counts.astype(float)})''',
  '''df=pd.DataFrame({'a':[1,None],'b':[None,None],'c':[0,2]}); result=missing_report(df)
assert result['missing_count'].tolist()==[1,2,0] and result['missing_fraction'].tolist()==[.5,1.,0.], 'Report counts and fractions separately.'
assert list(result.index)==['a','b','c'] and list(result.columns)==['missing_count','missing_fraction'], 'Keep a stable report schema.'
assert missing_report(df.iloc[:0])['missing_fraction'].tolist()==[0.,0.,0.], 'Handle zero input rows.' ''',
  "print(missing_report(pd.DataFrame({'a':[1,None],'b':[0,2]})))",'Compute isna().sum(); divide by row count only when nonzero.',packages=['pandas'])
q(c,'dedup','Resolve customer snapshots','Two CRM snapshots contain duplicate customers and tied update times.',
  'Stable sorting and an explicit tie-break determine the survivor. Parse timestamps before sorting; chronological sorting of mixed-offset text is unsafe. drop_duplicates keeps either first or last according to the order you establish.',
  'Implement customer_snapshot(df). Columns are customer_id, updated_at (offset-aware ISO text), value. Keep the latest timestamp per customer, breaking ties by later original row position. Return customer_id-sorted rows with a fresh RangeIndex, preserving the original columns and timestamp text. Do not mutate df.',
  'def customer_snapshot(df)',
  '''import pandas as pd
def customer_snapshot(df):
    out=df.copy()
    out['_time']=pd.to_datetime(out['updated_at'],utc=True,format='mixed')
    out['_position']=range(len(out))
    out=out.sort_values(['_time','_position']).drop_duplicates('customer_id',keep='last')
    return out.sort_values('customer_id').drop(columns=['_time','_position']).reset_index(drop=True)''',
  '''df=pd.DataFrame({'customer_id':['b','a','a','a'],'updated_at':['2026-01-01T00:00:00Z','2026-01-02T00:00:00Z','2026-01-01T00:00:00Z','2026-01-02T00:00:00Z'],'value':[1,2,3,4]}); result=customer_snapshot(df)
assert result['customer_id'].tolist()==['a','b'] and result['value'].tolist()==[4,1], 'Choose the latest timestamp and last position on ties.'
assert list(result.columns)==list(df.columns) and list(result.index)==[0,1] and len(df)==4, 'Keep schema, reset index, and preserve source.'
assert customer_snapshot(df.iloc[:0]).empty, 'Empty snapshots should remain empty.' ''',
  "print(customer_snapshot(pd.DataFrame({'customer_id':['a','a'],'updated_at':['2026-01-01T00:00:00Z','2026-01-02T00:00:00Z'],'value':[1,2]})))",'Add parsed time and original position as temporary columns, sort, deduplicate, and remove helpers.',packages=['pandas'])
q(c,'revenue','Net sales by region','Finance needs paid revenue less refunds, while canceled orders must contribute nothing.',
  'Specify the unit and sign convention before aggregating. Grouping should reflect business semantics, not just a convenient column. Filtering before groupby prevents unrelated statuses from silently affecting totals; negative refunds remain visible in the result.',
  'Implement net_sales(df) with region, status, amount columns. Include only paid and refunded rows. Paid amounts add and refunded amounts subtract; amounts are nonnegative. Return a DataFrame with region and net_revenue, sorted by region and reset index. Keep groups whose net is zero. Do not mutate input.',
  'def net_sales(df)',
  '''import pandas as pd
def net_sales(df):
    out=df[df['status'].isin(['paid','refunded'])].copy()
    out['net_revenue']=out['amount'].where(out['status']=='paid',-out['amount'])
    return out.groupby('region',as_index=False)['net_revenue'].sum().sort_values('region').reset_index(drop=True)''',
  '''df=pd.DataFrame({'region':['S','N','N','S'],'status':['paid','paid','refunded','canceled'],'amount':[10,20,5,99]}); result=net_sales(df)
assert result.to_dict('records')==[{'region':'N','net_revenue':15},{'region':'S','net_revenue':10}], 'Subtract refunds and exclude canceled orders.'
assert len(df)==4 and df.loc[2,'amount']==5, 'Do not change source amounts.'
assert list(net_sales(df.iloc[:0]).columns)==['region','net_revenue'], 'Preserve output schema for empty data.' ''',
  "print(net_sales(pd.DataFrame({'region':['N','N'],'status':['paid','refunded'],'amount':[20,5]})))",'Filter statuses, assign a signed amount, then group by region.',packages=['pandas'])
q(c,'join','Stop a join from multiplying money','A duplicate customer dimension can silently multiply order totals.',
  'A many-to-one join should not increase the number of left rows. pandas merge(validate="many_to_one") enforces unique right-hand keys. Detect orphan keys separately rather than dropping them with an inner join. This is a data contract, not just syntax.',
  'Implement attach_regions(orders, customers). orders has order_id, customer_id, amount; customers has customer_id, region. Left-join many-to-one. Raise ValueError for duplicated customer keys or unmatched orders. Return columns order_id,customer_id,amount,region in original order. Do not mutate inputs; keys are nonmissing.',
  'def attach_regions(orders, customers)',
  '''import pandas as pd
def attach_regions(orders, customers):
    out=orders.merge(customers,on='customer_id',how='left',sort=False,validate='many_to_one',indicator=True)
    if (out['_merge']!='both').any(): raise ValueError('Orphan order')
    return out[['order_id','customer_id','amount','region']]''',
  '''o=pd.DataFrame({'order_id':[2,1],'customer_id':['a','a'],'amount':[7,9]}); c=pd.DataFrame({'customer_id':['a'],'region':['N']})
assert attach_regions(o,c)['order_id'].tolist()==[2,1] and attach_regions(o,c)['amount'].sum()==16, 'Preserve row grain and order.'
try: attach_regions(o,pd.concat([c,c]))
except ValueError: pass
else: raise AssertionError('Reject a nonunique dimension.')
try: attach_regions(o,c.iloc[:0])
except ValueError: pass
else: raise AssertionError('Reject orphan keys rather than silently dropping them.')''',
  "print(attach_regions(pd.DataFrame({'order_id':[1],'customer_id':['a'],'amount':[9]}),pd.DataFrame({'customer_id':['a'],'region':['N']})))",'Use left merge with validate and indicator; reject any left_only row.',packages=['pandas'])
q(c,'daily','Fill a daily reporting calendar','A day with no orders is absent from the raw data, but must appear in the report.',
  'Resampling changes the time grain. Convert timestamps to UTC first, set a DatetimeIndex, aggregate by day, and fill gaps between the minimum and maximum observed day. A missing calendar day is zero revenue here; that policy is different from missing source amounts.',
  'Implement daily_revenue(df). Columns timestamp (offset-aware ISO text) and amount (finite numeric). Return a pandas Series of total amount per UTC calendar day, with a UTC DatetimeIndex, including zero-valued gaps between first and last observed day. For empty input, return an empty float Series with a UTC DatetimeIndex.',
  'def daily_revenue(df)',
  '''import pandas as pd
def daily_revenue(df):
    if df.empty: return pd.Series([],index=pd.DatetimeIndex([],tz='UTC'),dtype=float)
    out=df.copy()
    out['timestamp']=pd.to_datetime(out['timestamp'],utc=True,format='mixed')
    return out.set_index('timestamp')['amount'].resample('D').sum()''',
  '''df=pd.DataFrame({'timestamp':['2026-01-03T01:00:00Z','2026-01-01T01:00:00Z','2026-01-01T02:00:00Z'],'amount':[9,2,3]}); s=daily_revenue(df)
assert s.tolist()==[5,0,9], 'Aggregate duplicate days and fill calendar gaps.'
assert str(s.index.tz)=='UTC' and s.index[0].day==1 and len(df)==3, 'Return a UTC daily index without source mutation.'
assert daily_revenue(df.iloc[:0]).empty and str(daily_revenue(df.iloc[:0]).index.tz)=='UTC', 'Preserve the index type for empty input.' ''',
  "print(daily_revenue(pd.DataFrame({'timestamp':['2026-01-01T12:00:00Z','2026-01-03T12:00:00Z'],'amount':[5,9]})))",'Parse UTC timestamps, set the index, and resample with D.',packages=['pandas'])
q(c,'lag','Previous purchase, per customer','A retention analysis needs the previous purchase amount, without mixing customers.',
  'shift must operate inside each customer group after establishing chronological order. A global shift leaks values across customers. Return rows in their original order so downstream code can align the derived column safely.',
  'Implement previous_amount(df). Columns customer_id, timestamp (ISO UTC text), amount. Add previous_amount for the preceding event of that customer sorted by timestamp, tie-breaking by original row position. First events get NaN. Return the original row order and index, plus the new column; do not mutate input.',
  'def previous_amount(df)',
  '''import pandas as pd
def previous_amount(df):
    out=df.copy()
    out['_position']=range(len(out))
    out=out.sort_values(['customer_id','timestamp','_position'])
    out['previous_amount']=out.groupby('customer_id')['amount'].shift(1)
    return out.sort_values('_position').drop(columns='_position')''',
  '''df=pd.DataFrame({'customer_id':['a','b','a'],'timestamp':['2026-01-02','2026-01-01','2026-01-01'],'amount':[20,7,10]},index=[9,4,2]); result=previous_amount(df)
assert result.loc[9,'previous_amount']==10 and pd.isna(result.loc[4,'previous_amount']), 'Shift within customer, not globally.'
assert list(result.index)==[9,4,2] and 'previous_amount' not in df, 'Preserve row identity and source schema.'
assert previous_amount(df.iloc[:0]).empty, 'Handle empty events.' ''',
  "print(previous_amount(pd.DataFrame({'customer_id':['a','a'],'timestamp':['2026-01-01','2026-01-02'],'amount':[10,20]})))",'Add an original position, sort within customer, groupby.shift(), then restore order.',packages=['pandas'])
q(c,'cohort','Project: day-one retention','A product manager wants the fraction of signup-day users who return on the next calendar day.',
  'Cohort analysis uses unique users, not event counts. Repeated events must not inflate the denominator or retained count. Define day one as the calendar day after the first activity date in UTC; this is not a rolling 24-hour window.',
  'Implement day_one_retention(df), with user_id and timestamp (offset-aware ISO text). Return a float fraction of unique users who have an event on the UTC day after their first event. Return None for no users. Multiple events per user/day count once. Do not mutate input.',
  'def day_one_retention(df)',
  '''import pandas as pd
def day_one_retention(df):
    if df.empty: return None
    out=df.copy()
    out['day']=pd.to_datetime(out['timestamp'],utc=True,format='mixed').dt.floor('D')
    first=out.groupby('user_id')['day'].transform('min')
    retained=out.loc[out['day']==first+pd.Timedelta(days=1),'user_id'].nunique()
    return float(retained/out['user_id'].nunique())''',
  '''df=pd.DataFrame({'user_id':['a','a','a','b','b'],'timestamp':['2026-01-01T23:00:00Z','2026-01-02T01:00:00Z','2026-01-02T03:00:00Z','2026-01-01T00:00:00Z','2026-01-03T00:00:00Z']})
assert day_one_retention(df)==.5, 'Deduplicate users and use next calendar day.'
assert day_one_retention(df.iloc[:0]) is None, 'An empty cohort has no defined retention.'
assert day_one_retention(pd.DataFrame({'user_id':['x','x'],'timestamp':['2026-01-01T23:00:00-02:00','2026-01-02T02:00:00Z']}))==0., 'Convert to UTC before determining days.' ''',
  "print(day_one_retention(pd.DataFrame({'user_id':['a','a','b'],'timestamp':['2026-01-01T00:00:00Z','2026-01-02T00:00:00Z','2026-01-01T00:00:00Z']})))  # 0.5",'Compute each user’s first UTC day with transform, then count distinct users returning on first + 1 day.',packages=['pandas'],project=True)

c=course('sql-python','SQL from Python','Query, join, rank, and update data safely using a real in-memory SQLite database.','Working analyst','🗃️','#e4c68b')
q(c,'parameters','A safe customer lookup','A dashboard receives a customer name from a text box.',
  'Never interpolate user values into SQL text. DB-API placeholders bind values separately from the query. This protects quoting and query structure. A connection is supplied by the caller; do not close it inside a helper.',
  'Implement customer_orders(conn, customer). Table orders has id INTEGER, customer TEXT, amount REAL. Return a list of (id, amount) tuples for that exact customer, sorted by id. Use a parameterized SELECT. Do not modify the database or close conn.',
  'def customer_orders(conn, customer)',
  '''def customer_orders(conn, customer):
    return conn.execute('SELECT id, amount FROM orders WHERE customer = ? ORDER BY id',(customer,)).fetchall()''',
  '''import sqlite3
conn=sqlite3.connect(':memory:'); conn.execute('CREATE TABLE orders(id INTEGER,customer TEXT,amount REAL)'); conn.executemany('INSERT INTO orders VALUES(?,?,?)',[(2,"O\'Neil",5),(1,"O\'Neil",3),(3,'Ada',7)])
assert customer_orders(conn,"O'Neil")==[(1,3.0),(2,5.0)], 'Names containing quotes must work.'
assert customer_orders(conn,"' OR 1=1 --")==[], 'Bind the customer value; never interpolate SQL.'
assert conn.execute('SELECT COUNT(*) FROM orders').fetchone()[0]==3, 'Keep the connection open and data unchanged.'
conn.close()''',
  '# Tables and connections are supplied by the exercise checks.\n# Define customer_orders; then choose Check answer.', 'Use WHERE customer = ? and pass a one-element tuple.')
q(c,'aggregate','Customers above a revenue threshold','Sales wants customers whose completed order revenue clears a minimum.',
  'WHERE filters input rows before grouping; HAVING filters aggregated groups. SUM ignores NULL amounts, but a group containing only NULL values sums to NULL unless COALESCE defines a fallback. Bind thresholds as parameters.',
  'Implement revenue_customers(conn, minimum). orders(customer TEXT, status TEXT, amount REAL). Include status=paid only, treat NULL amount as 0, and return (customer,total) tuples with total >= minimum, sorted by total descending then customer ascending. Customers without paid rows do not appear.',
  'def revenue_customers(conn, minimum)',
  '''def revenue_customers(conn, minimum):
    return conn.execute("SELECT customer, SUM(COALESCE(amount,0)) AS total FROM orders WHERE status='paid' GROUP BY customer HAVING SUM(COALESCE(amount,0)) >= ? ORDER BY total DESC, customer ASC",(minimum,)).fetchall()''',
  '''import sqlite3
conn=sqlite3.connect(':memory:'); conn.execute('CREATE TABLE orders(customer TEXT,status TEXT,amount REAL)'); conn.executemany('INSERT INTO orders VALUES(?,?,?)',[('b','paid',10),('a','paid',5),('a','paid',5),('a','canceled',90),('c','paid',None)])
assert revenue_customers(conn,10)==[('a',10),('b',10)], 'Aggregate paid rows and use a deterministic tie break.'
assert revenue_customers(conn,11)==[], 'Filter aggregate totals using the threshold.'
assert revenue_customers(conn,0)[-1]==('c',0), 'Handle all-NULL amounts explicitly.'
conn.close()''',
  '# Implement the query helper. The checks create the orders table.', 'Use WHERE, GROUP BY, HAVING, and two ORDER BY keys.')
q(c,'leftjoin','Customers who never ordered','A customer base report must include people with no purchases.',
  'A left join retains every customer. COUNT(*) counts the unmatched placeholder row, so count a nonnullable order key instead. COALESCE turns missing aggregate revenue into zero. Group by a stable identifier rather than a potentially duplicated display name.',
  'Implement customer_summary(conn). customers(id INTEGER PRIMARY KEY,name TEXT); orders(id INTEGER PRIMARY KEY,customer_id INTEGER,amount REAL). Return (customer_id, order_count, total_amount) for every customer, ordered by customer_id. Missing orders contribute count=0 and amount=0.',
  'def customer_summary(conn)',
  '''def customer_summary(conn):
    return conn.execute('SELECT c.id, COUNT(o.id), COALESCE(SUM(o.amount),0) FROM customers c LEFT JOIN orders o ON o.customer_id=c.id GROUP BY c.id ORDER BY c.id').fetchall()''',
  '''import sqlite3
conn=sqlite3.connect(':memory:'); conn.executescript('CREATE TABLE customers(id INTEGER PRIMARY KEY,name TEXT); CREATE TABLE orders(id INTEGER PRIMARY KEY,customer_id INTEGER,amount REAL);'); conn.executemany('INSERT INTO customers VALUES(?,?)',[(1,'Ada'),(2,'Ada'),(3,'Bob')]);conn.executemany('INSERT INTO orders VALUES(?,?,?)',[(1,1,5),(2,1,7),(3,3,0)])
assert customer_summary(conn)==[(1,2,12),(2,0,0),(3,1,0)], 'Count order IDs and preserve customers with no purchases.'
assert len(customer_summary(conn))==3, 'Identical customer names must remain distinct.'
conn.execute('DELETE FROM orders')
assert all(row[1:]==(0,0) for row in customer_summary(conn)), 'An empty fact table still returns all customers.'
conn.close()''',
  '# Implement customer_summary(conn); checks create the dimension and fact tables.', 'LEFT JOIN on customer_id, COUNT(o.id), and COALESCE(SUM(...),0).')
q(c,'window','Latest event without a lossy groupby','An events table has several states per account, including timestamp ties.',
  'MAX(timestamp) alongside unrelated nonaggregated columns does not express a portable survivor rule. ROW_NUMBER assigns a ranking within each entity. Order by timestamp descending and a unique event key descending to resolve ties.',
  'Implement latest_events(conn). events(event_id INTEGER PRIMARY KEY,account_id TEXT,occurred_at TEXT,status TEXT). Timestamps use fixed-format UTC strings. Return (account_id,status) for the latest event per account; on equal times choose greatest event_id. Sort by account_id.',
  'def latest_events(conn)',
  '''def latest_events(conn):
    return conn.execute('WITH ranked AS (SELECT account_id,status,ROW_NUMBER() OVER(PARTITION BY account_id ORDER BY occurred_at DESC,event_id DESC) AS rn FROM events) SELECT account_id,status FROM ranked WHERE rn=1 ORDER BY account_id').fetchall()''',
  '''import sqlite3
conn=sqlite3.connect(':memory:'); conn.execute('CREATE TABLE events(event_id INTEGER PRIMARY KEY,account_id TEXT,occurred_at TEXT,status TEXT)');conn.executemany('INSERT INTO events VALUES(?,?,?,?)',[(1,'a','2026-01-02','open'),(2,'a','2026-01-01','closed'),(3,'a','2026-01-02','paused'),(4,'b','2026-01-01','open')])
assert latest_events(conn)==[('a','paused'),('b','open')], 'Rank by event time and then event_id.'
conn.execute("INSERT INTO events VALUES(5,'a','2026-01-03','closed')")
assert latest_events(conn)[0]==('a','closed'), 'Later time wins over previous status.'
conn.execute('DELETE FROM events'); assert latest_events(conn)==[], 'Handle an empty table.'
conn.close()''',
  '# Implement latest_events(conn) using a window function.', 'Compute ROW_NUMBER in a CTE and filter rn=1 outside it.')
q(c,'running','A running balance with deterministic order','An account can have several transactions at the exact same timestamp.',
  'Window frames matter. An explicit ROWS frame accumulates row by row; ordering must contain a unique tie-breaker. Signed amounts let deposits and withdrawals use the same cumulative SUM.',
  'Implement running_balances(conn). transactions(id INTEGER PRIMARY KEY,account_id TEXT,ts TEXT,amount REAL). Return (id,account_id,balance) sorted by account_id,ts,id. Balance is cumulative signed amount within account, ordered by ts then id, using an explicit ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW frame.',
  'def running_balances(conn)',
  '''def running_balances(conn):
    return conn.execute('SELECT id,account_id,SUM(amount) OVER(PARTITION BY account_id ORDER BY ts,id ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) FROM transactions ORDER BY account_id,ts,id').fetchall()''',
  '''import sqlite3
conn=sqlite3.connect(':memory:');conn.execute('CREATE TABLE transactions(id INTEGER PRIMARY KEY,account_id TEXT,ts TEXT,amount REAL)');conn.executemany('INSERT INTO transactions VALUES(?,?,?,?)',[(2,'a','2026-01-01',-3),(1,'a','2026-01-01',10),(3,'b','2026-01-01',5)])
assert running_balances(conn)==[(1,'a',10),(2,'a',7),(3,'b',5)], 'Use deterministic row order and separate account partitions.'
conn.execute("INSERT INTO transactions VALUES(4,'a','2026-01-02',2)")
assert running_balances(conn)[2]==(4,'a',9), 'Carry forward the prior balance.'
conn.execute('DELETE FROM transactions');assert running_balances(conn)==[], 'Handle empty transactions.'
conn.close()''',
  '# Implement running_balances(conn).', 'Use SUM OVER with PARTITION BY account_id, ORDER BY ts,id, and an explicit ROWS frame.')
q(c,'rank','Top products with ties','Merchandising asks for the top two revenue ranks per category, including ties.',
  'ROW_NUMBER chooses a fixed number of rows; DENSE_RANK includes all ties at a rank. Aggregate product revenue first, then rank products within each category. The rank ordering must use revenue only or equal-revenue products will stop tying.',
  'Implement top_products(conn, n). sales(category TEXT,product TEXT,revenue REAL). Sum revenue by category/product, dense-rank totals descending per category, and include rank <= n. Return (category,product,total) sorted by category, total descending, product ascending. Return [] for n <= 0.',
  'def top_products(conn, n)',
  '''def top_products(conn, n):
    if n<=0: return []
    return conn.execute('WITH totals AS (SELECT category,product,SUM(revenue) AS total FROM sales GROUP BY category,product), ranked AS (SELECT *,DENSE_RANK() OVER(PARTITION BY category ORDER BY total DESC) AS r FROM totals) SELECT category,product,total FROM ranked WHERE r<=? ORDER BY category,total DESC,product',(n,)).fetchall()''',
  '''import sqlite3
conn=sqlite3.connect(':memory:');conn.execute('CREATE TABLE sales(category TEXT,product TEXT,revenue REAL)');conn.executemany('INSERT INTO sales VALUES(?,?,?)',[('A','x',5),('A','x',5),('A','y',10),('A','z',3),('B','w',1)])
assert top_products(conn,1)==[('A','x',10),('A','y',10),('B','w',1)], 'Include ties at the same dense rank.'
assert len(top_products(conn,2))==4, 'Second rank follows tied first rank without a gap.'
assert top_products(conn,0)==[], 'Nonpositive n returns no products.'
conn.close()''',
  '# Implement top_products(conn, n).', 'Use an aggregate CTE followed by DENSE_RANK, then filter in an outer SELECT.')
q(c,'retention','SQL day-one retention','A product data mart needs retention without exporting every event to Python.',
  'Reduce timestamp events to distinct user-days before computing cohorts. Joining first-day users to the next day must count unique users, not activity rows. SQLite date functions work here because dates are already normalized UTC YYYY-MM-DD strings.',
  'Implement retention_sql(conn). activity(user_id TEXT,day TEXT) may contain duplicates. Return the fraction of distinct users active on the day after their first day. Return None for an empty table. Use SQL to compute the metric.',
  'def retention_sql(conn)',
  '''def retention_sql(conn):
    return conn.execute("WITH firsts AS (SELECT user_id,MIN(day) AS first_day FROM activity GROUP BY user_id) SELECT AVG(CASE WHEN EXISTS(SELECT 1 FROM activity a WHERE a.user_id=f.user_id AND a.day=date(f.first_day,'+1 day')) THEN 1.0 ELSE 0.0 END) FROM firsts f").fetchone()[0]''',
  '''import sqlite3
conn=sqlite3.connect(':memory:');conn.execute('CREATE TABLE activity(user_id TEXT,day TEXT)');conn.executemany('INSERT INTO activity VALUES(?,?)',[('a','2026-01-01'),('a','2026-01-02'),('a','2026-01-02'),('b','2026-01-01'),('b','2026-01-03')])
assert retention_sql(conn)==.5, 'Duplicate activity cannot inflate retention.'
conn.execute("INSERT INTO activity VALUES('b','2026-01-02')");assert retention_sql(conn)==1., 'Count each retained user exactly once.'
conn.execute('DELETE FROM activity');assert retention_sql(conn) is None, 'Empty populations have no defined retention.'
conn.close()''',
  '# Implement retention_sql(conn). Dates are pre-normalized UTC days.', 'Aggregate first days, use EXISTS for next-day activity, then AVG a zero/one indicator.')
q(c,'transaction','Project: load a batch atomically','A loader must insert or update events without leaving half a batch behind after an error.',
  'Idempotent writes use a stable primary key. Transactions group writes so success commits all changes and failure rolls them back. Here conn has no pending transaction at entry, and the function owns the transaction for this batch.',
  'Implement load_events(conn, rows). events(id TEXT PRIMARY KEY,amount REAL NOT NULL CHECK(amount>=0)) already exists. rows is a list of (id, amount) tuples. Upsert each row; on conflict replace amount. Commit on success; on any write error roll back the entire batch and re-raise the error. Keep conn open. Replaying a successful batch must not duplicate events.',
  'def load_events(conn, rows)',
  '''def load_events(conn, rows):
    with conn:
        conn.executemany('INSERT INTO events(id,amount) VALUES(?,?) ON CONFLICT(id) DO UPDATE SET amount=excluded.amount',rows)''',
  '''import sqlite3
conn=sqlite3.connect(':memory:');conn.execute('CREATE TABLE events(id TEXT PRIMARY KEY,amount REAL NOT NULL CHECK(amount>=0))')
load_events(conn,[('a',5)]);load_events(conn,[('a',7),('b',2)]);load_events(conn,[('a',7),('b',2)])
assert conn.execute('SELECT * FROM events ORDER BY id').fetchall()==[('a',7),('b',2)], 'Upsert by stable key and support replay.'
try: load_events(conn,[('a',99),('c',-1)])
except sqlite3.IntegrityError: pass
else: raise AssertionError('Do not swallow the failed write.')
assert conn.execute("SELECT amount FROM events WHERE id='a'").fetchone()[0]==7, 'Roll back earlier writes when a later row fails.'
assert conn.execute('SELECT COUNT(*) FROM events').fetchone()[0]==2, 'Keep the connection usable after rollback.'
conn.close()''',
  '# Implement load_events(conn, rows). Checks include a deliberate constraint failure.', 'Use with conn: around a parameterized executemany upsert.',project=True)

c=course('analytics-lab','Analytical Thinking & ML Evaluation','Build defensible metrics, avoid data leakage, and evaluate results honestly.','Year 1–2','📊','#f0b5cf')
q(c,'funnel','A conversion rate with a real denominator','Tracking logs contain repeat visits and duplicate purchases from the same user.',
  'Metrics depend on the counting unit. Here the unit is a distinct visitor, and converters must also belong to the visitor population. An empty denominator means an undefined rate, not evidence of poor conversion.',
  'Implement conversion_rate(visitors, buyers). Inputs are iterables of user IDs, possibly repeated. Return the fraction of distinct visitors also present in buyers. Ignore buyers not present in visitors. Return None for no visitors.',
  'def conversion_rate(visitors, buyers)',
  '''def conversion_rate(visitors, buyers):
    v,b=set(visitors),set(buyers)
    return len(v & b)/len(v) if v else None''',
  '''assert conversion_rate(['a','a','b'],['a','a','outside'])==.5, 'Count users, not events, and use the eligible population.'
assert conversion_rate([],['x']) is None, 'An empty denominator is undefined.'
assert conversion_rate(iter(['a','b']),iter([]))==0., 'Support one-pass sources and genuine zero conversions.' ''',
  "print(conversion_rate(['a','a','b'],['a']))  # 0.5",'Convert both populations to sets, intersect, then divide by unique visitors.')
q(c,'confusion','Accuracy hides the expensive error','A fraud model catches some fraud while falsely blocking legitimate payments.',
  'Precision measures how many predicted positives are correct; recall measures how many actual positives were found. The appropriate trade-off depends on business costs. Define division-by-zero policy instead of letting a metric crash on a small batch.',
  'Implement classification_report(actual, predicted). Equal-length lists contain 0 or 1. Return a dict with tp,fp,fn,tn,precision,recall. Use None for precision/recall with a zero denominator. Counts are integer. Inputs may be empty.',
  'def classification_report(actual, predicted)',
  '''def classification_report(actual, predicted):
    tp=sum(a==1 and p==1 for a,p in zip(actual,predicted))
    fp=sum(a==0 and p==1 for a,p in zip(actual,predicted))
    fn=sum(a==1 and p==0 for a,p in zip(actual,predicted))
    tn=sum(a==0 and p==0 for a,p in zip(actual,predicted))
    return dict(tp=tp,fp=fp,fn=fn,tn=tn,precision=tp/(tp+fp) if tp+fp else None,recall=tp/(tp+fn) if tp+fn else None)''',
  '''assert classification_report([1,1,0,0],[1,0,1,0])==dict(tp=1,fp=1,fn=1,tn=1,precision=.5,recall=.5), 'Use the correct precision and recall denominators.'
assert classification_report([0,0],[0,0])==dict(tp=0,fp=0,fn=0,tn=2,precision=None,recall=None), 'Represent undefined metrics explicitly.'
assert classification_report([],[])==dict(tp=0,fp=0,fn=0,tn=0,precision=None,recall=None), 'Handle empty evaluation batches.' ''',
  'print(classification_report([1,1,0,0], [1,0,1,0]))','Count all four combinations, then calculate precision from tp+fp and recall from tp+fn.')
q(c,'micro','Do not average campaign rates blindly','Two campaigns have very different traffic volumes.',
  'Macro averages weight each group equally; micro rates pool all successes and trials. Both can be meaningful, but answer different questions. Exclude zero-exposure groups from macro rates and retain them as zero contribution in pooled counts.',
  'Implement campaign_rates(rows). Each row is (successes,trials), with valid nonnegative counts and successes <= trials. Return (macro,micro), using only positive-trial rows in macro. Return None for either rate if its denominator is absent.',
  'def campaign_rates(rows)',
  '''def campaign_rates(rows):
    rates=[s/n for s,n in rows if n>0]
    trials=sum(n for s,n in rows)
    return (sum(rates)/len(rates) if rates else None, sum(s for s,n in rows)/trials if trials else None)''',
  '''macro,micro=campaign_rates([(1,2),(9,90),(0,0)])
assert abs(macro-.3)<1e-12 and abs(micro-10/92)<1e-12, 'Distinguish an average of rates from a ratio of totals.'
assert campaign_rates([])==(None,None) and campaign_rates([(0,0)])==(None,None), 'Handle no-exposure cases.'
assert campaign_rates([(0,10)])==(0.,0.), 'Zero conversions with traffic is a defined zero rate.' ''',
  'print(campaign_rates([(1,2),(9,90)]))','Compute per-group rates separately from summed successes and trials.')
q(c,'split','A time split that respects causality','A forecasting pipeline must not learn from records dated after the evaluation cutoff.',
  'Random splitting can leak future behavior into historical predictions. A chronological cutoff makes the information boundary explicit. Here dates are already normalized YYYY-MM-DD strings, and the cutoff is inclusive on the training side.',
  'Implement time_split(rows, cutoff). Each row is a dict with day and any other fields. Return (train,test) lists: day <= cutoff is train, later is test. Preserve order within each result and copy each row dictionary. Do not mutate input.',
  'def time_split(rows, cutoff)',
  '''def time_split(rows, cutoff):
    return ([dict(r) for r in rows if r['day']<=cutoff],[dict(r) for r in rows if r['day']>cutoff])''',
  '''rows=[{'day':'2026-01-03','x':3},{'day':'2026-01-01','x':1},{'day':'2026-01-02','x':2}]
train,test=time_split(rows,'2026-01-02')
assert [r['x'] for r in train]==[1,2] and [r['x'] for r in test]==[3], 'Use an inclusive training cutoff and stable order.'
train[0]['x']=99;assert rows[1]['x']==1, 'Return independent row dictionaries.'
assert time_split([],'2026-01-01')==([],[]), 'Handle no observations.' ''',
  "print(time_split([{'day':'2026-01-01'},{'day':'2026-01-03'}], '2026-01-02'))",'Partition on day <= cutoff, copying the selected row dicts.')
q(c,'train-scale','Fit preprocessing on training data only','A new customer has a value much larger than the training population.',
  'Computing means on the combined train/test table leaks evaluation information. Learn parameters on train, then reuse them unchanged for test. A constant training column uses scale 1; a different test value should not be forced to zero.',
  'Implement scale_train_test(train, test). Inputs are nonempty 2-D training data and 2-D test data with matching feature count. Return (scaled_train,scaled_test), using training means and population standard deviations only; replace zero std with 1. Do not mutate inputs.',
  'def scale_train_test(train, test)',
  '''import numpy as np
def scale_train_test(train, test):
    tr,te=np.asarray(train,dtype=float),np.asarray(test,dtype=float)
    mean,std=tr.mean(axis=0),tr.std(axis=0)
    scale=np.where(std==0,1,std)
    return (tr-mean)/scale,(te-mean)/scale''',
  '''train=np.array([[0.,5.],[2.,5.]]);test=np.array([[100.,7.]])
a,b=scale_train_test(train,test)
assert np.allclose(a,[[-1,0],[1,0]]) and np.allclose(b,[[99,2]]), 'Fit statistics on training rows only.'
assert train[0,0]==0 and test[0,0]==100, 'Do not mutate either split.'
assert scale_train_test([[1]],np.empty((0,1)))[1].shape==(0,1), 'Allow an empty test split.' ''',
  'print(scale_train_test([[0,5],[2,5]], [[100,7]]))','Compute mean/std from train and apply the same arrays to both splits.',packages=['numpy'])
q(c,'interval','A confidence interval is not a certainty','An analyst estimates the mean order value from a small random sample.',
  'An approximate normal 95% interval is mean ± 1.96 * sample_std / sqrt(n). This approximation assumes independent observations and is weaker for small or highly skewed samples. It is not a prediction interval for the next order and does not fix biased sampling.',
  'Implement mean_interval(values). Return (mean,lower,upper) using sample standard deviation (ddof=1) and 1.96. Return None for fewer than two observations. Inputs are finite numeric values. Do not round the result.',
  'def mean_interval(values)',
  '''import math, statistics
def mean_interval(values):
    if len(values)<2: return None
    mean=statistics.mean(values)
    margin=1.96*statistics.stdev(values)/math.sqrt(len(values))
    return mean,mean-margin,mean+margin''',
  '''import math
mean,lo,hi=mean_interval([1,2,3,4])
assert mean==2.5 and abs((hi-lo)/2-1.96*math.sqrt(5/3)/2)<1e-12, 'Use the sample standard deviation and standard error.'
assert mean_interval([]) is None and mean_interval([5]) is None, 'A single observation cannot estimate sample variation.'
assert mean_interval([7,7,7])==(7,7,7), 'A constant sample has zero estimated standard error.' ''',
  'print(mean_interval([1,2,3,4]))','statistics.stdev uses sample variance; divide by sqrt(n).')
q(c,'baseline','Beat an honest forecasting baseline','A forecasting model should be compared against the last available observation.',
  'For a one-step persistence baseline, predict value[t] using value[t-1]. Using the current observation itself would give a deceptively perfect score. Mean absolute error measures average magnitude without canceling positive and negative errors.',
  'Implement persistence_mae(values). Return the mean absolute difference between consecutive observations, or None for fewer than two values. Inputs are finite numeric values in chronological order.',
  'def persistence_mae(values)',
  '''def persistence_mae(values):
    if len(values)<2: return None
    return sum(abs(values[i]-values[i-1]) for i in range(1,len(values)))/(len(values)-1)''',
  '''assert persistence_mae([10,12,9,15])==11/3, 'Compare each value with the previous observation.'
assert persistence_mae([]) is None and persistence_mae([4]) is None, 'No forecast errors exist before the second observation.'
assert persistence_mae([5,5,5])==0 and persistence_mae([-3,1])==4, 'Handle constant and signed series.' ''',
  'print(persistence_mae([10,12,9,15]))  # 3.666...', 'Build absolute one-step errors and divide by n-1.')
q(c,'experiment','Project: experiment results with guardrails','A checkout experiment improves conversion but also increases payment failures.',
  'An experiment decision needs more than a positive lift. Here we compute descriptive conversion lift and apply a predeclared error-rate guardrail. These checks do not establish statistical significance or causal validity; randomization, sample size, duration, and uncertainty still require review.',
  'Implement experiment_summary(control, treatment, max_error_rate). Each arm is a dict with visitors, conversions, errors. Return a dict with control_rate,treatment_rate,absolute_lift,relative_lift,guardrail_ok. Rates are None for zero visitors. absolute_lift is None if either rate undefined; relative_lift is None if control rate is zero/undefined or treatment undefined. guardrail_ok is True only when treatment visitors > 0 and treatment errors/visitors <= max_error_rate. All counts are valid.',
  'def experiment_summary(control, treatment, max_error_rate)',
  '''def experiment_summary(control, treatment, max_error_rate):
    a=control['conversions']/control['visitors'] if control['visitors'] else None
    b=treatment['conversions']/treatment['visitors'] if treatment['visitors'] else None
    lift=b-a if a is not None and b is not None else None
    return dict(control_rate=a,treatment_rate=b,absolute_lift=lift,relative_lift=lift/a if a not in (None,0) and lift is not None else None,guardrail_ok=bool(treatment['visitors'] and treatment['errors']/treatment['visitors']<=max_error_rate))''',
  '''a={'visitors':100,'conversions':10,'errors':1};b={'visitors':100,'conversions':15,'errors':8};r=experiment_summary(a,b,.05)
assert abs(r['absolute_lift']-.05)<1e-12 and abs(r['relative_lift']-.5)<1e-12 and not r['guardrail_ok'], 'Positive lift cannot hide a failed guardrail.'
z={'visitors':0,'conversions':0,'errors':0};r=experiment_summary(z,z,.05)
assert r['absolute_lift'] is None and r['relative_lift'] is None and not r['guardrail_ok'], 'Do not call an empty experiment successful.'
r=experiment_summary({'visitors':10,'conversions':0,'errors':0},{'visitors':10,'conversions':1,'errors':0},.05)
assert r['relative_lift'] is None and r['guardrail_ok'], 'Relative lift is undefined from a zero baseline.' ''',
  "print(experiment_summary({'visitors':100,'conversions':10,'errors':1}, {'visitors':100,'conversions':15,'errors':8}, .05))",'Calculate both rates first, guard undefined arithmetic, and evaluate errors separately.',project=True)

c=course('pipelines','Reliable Data Pipelines','Build loaders that can be retried, resumed, monitored, and trusted.','Year 1–2','🔄','#a6d9ba')
q(c,'quarantine','Quarantine invalid records','A source batch contains malformed records, but valid rows should still be recoverable.',
  'Validation should return actionable reasons rather than silently discarding rows. Separate structural checks from conversions and define a priority when a row violates multiple rules. Preserve raw records in quarantine so they can be investigated.',
  'Implement validate_batch(rows). Return (valid,rejected). Valid rows require a nonblank string id and an amount that is an int/float (not bool), finite, and >= 0. rejected contains (zero_based_index, reason), with reason id or amount; id takes priority. Return copies of valid rows and do not mutate input.',
  'def validate_batch(rows)',
  '''import math
def validate_batch(rows):
    valid,rejected=[],[]
    for i,row in enumerate(rows):
        if not isinstance(row.get('id'),str) or not row['id'].strip():
            rejected.append((i,'id'));continue
        a=row.get('amount')
        if isinstance(a,bool) or not isinstance(a,(int,float)) or not math.isfinite(a) or a<0:
            rejected.append((i,'amount'));continue
        valid.append(dict(row))
    return valid,rejected''',
  '''rows=[{'id':'a','amount':0},{'id':'','amount':-1},{'id':'b','amount':True},{'id':'c','amount':float('nan')},{'id':'d','amount':'3'}]
v,r=validate_batch(rows)
assert v==[{'id':'a','amount':0}] and r==[(1,'id'),(2,'amount'),(3,'amount'),(4,'amount')], 'Validate types, missing keys, finiteness, and reason priority.'
v[0]['amount']=4;assert rows[0]['amount']==0, 'Do not return mutable source dictionaries.'
assert validate_batch([])==([],[]), 'Handle an empty batch.' ''',
  "print(validate_batch([{'id':'a','amount':0},{'id':'b','amount':-1}]))",'Check the id first; bool is a subclass of int, so explicitly exclude it.')
q(c,'pagination','Fetch every API page exactly once','A cursor-based API can return an empty page that still points to more data.',
  'Pagination ends when the cursor says it ends, not when a page has no items. Track visited cursors to detect accidental cycles. A supplied fake fetch function makes this behavior testable without network access or credentials.',
  'Implement collect_pages(fetch_page). Call fetch_page(cursor), starting with None. Each response has items (list) and next_cursor (string or None). Concatenate items in page order until next_cursor is None. Raise ValueError if a cursor would repeat. Empty pages with a non-None cursor must not terminate early.',
  'def collect_pages(fetch_page)',
  '''def collect_pages(fetch_page):
    cursor=None;seen=set();items=[]
    while True:
        if cursor in seen: raise ValueError('cursor cycle')
        seen.add(cursor)
        page=fetch_page(cursor);items.extend(page['items'])
        cursor=page['next_cursor']
        if cursor is None: return items''',
  '''calls=[]
pages={None:{'items':[1],'next_cursor':'a'},'a':{'items':[],'next_cursor':'b'},'b':{'items':[2,3],'next_cursor':None}}
def fetch(cursor):
    calls.append(cursor);return pages[cursor]
assert collect_pages(fetch)==[1,2,3] and calls==[None,'a','b'], 'Follow cursors through empty pages without duplicate requests.'
assert collect_pages(lambda c:{'items':[],'next_cursor':None})==[], 'Handle a truly empty source.'
try: collect_pages(lambda c:{'items':[],'next_cursor':'same'})
except ValueError: pass
else: raise AssertionError('Detect repeated cursors.')''',
  "print(collect_pages(lambda cursor: {'items':[1,2], 'next_cursor':None}))",'Loop on next_cursor; check the cursor against a seen set before fetching.')
q(c,'retry','Retry transient failures only','A data download occasionally times out; a malformed request should fail immediately.',
  'Retries are appropriate for transient failures, with a bounded attempt count. Permanent failures should propagate. A sleeper dependency lets tests verify exponential backoff without waiting. Real systems often add jitter and respect server retry guidance; writes also need idempotency.',
  'Implement retry_call(operation, attempts, sleep). Call operation() until success or attempts are exhausted. Retry only TimeoutError. Between attempts call sleep(2**retry_index), yielding delays 1,2,4,...; never sleep after the final failure. Re-raise the final exception. Raise ValueError for attempts < 1. Do not actually import or call time.sleep.',
  'def retry_call(operation, attempts, sleep)',
  '''def retry_call(operation, attempts, sleep):
    if attempts<1: raise ValueError('positive attempts required')
    for i in range(attempts):
        try: return operation()
        except TimeoutError:
            if i==attempts-1: raise
            sleep(2**i)''',
  '''state={'calls':0};delays=[]
def operation():
    state['calls']+=1
    if state['calls']<3: raise TimeoutError('temporary')
    return 7
assert retry_call(operation,3,delays.append)==7 and delays==[1,2], 'Bound attempts and back off between failures.'
try: retry_call(lambda: (_ for _ in ()).throw(ValueError('permanent')),3,delays.append)
except ValueError: pass
else: raise AssertionError('Do not retry permanent errors.')
failed=[]
try: retry_call(lambda: (_ for _ in ()).throw(TimeoutError()),2,failed.append)
except TimeoutError: pass
else: raise AssertionError('Re-raise exhausted transient failures.')
assert failed==[1], 'Never sleep after the final attempt.' ''',
  'print(retry_call(lambda: 42, 3, lambda seconds: None))  # 42','Catch only TimeoutError; delay only if another attempt remains.')
q(c,'watermark','Late data behind a checkpoint','A source can deliver updates after their event time has passed.',
  'A high-water mark without an overlap misses late events. Re-read a small lookback window, then deduplicate downstream by stable key. Advance the checkpoint only after successful persistence in a real pipeline; this function merely selects the candidate batch.',
  'Implement select_window(rows, checkpoint, lookback). Each row has integer ts and other fields. Return copied rows with ts >= checkpoint-lookback, preserving order, and a new checkpoint equal to max(old checkpoint, selected timestamps). Return (selected,new_checkpoint). Raise ValueError if lookback < 0. Do not mutate rows.',
  'def select_window(rows, checkpoint, lookback)',
  '''def select_window(rows, checkpoint, lookback):
    if lookback<0: raise ValueError('negative lookback')
    selected=[dict(r) for r in rows if r['ts']>=checkpoint-lookback]
    return selected,max([checkpoint]+[r['ts'] for r in selected])''',
  '''rows=[{'ts':94,'id':'old'},{'ts':95,'id':'late'},{'ts':103,'id':'new'}];selected,cp=select_window(rows,100,5)
assert [r['id'] for r in selected]==['late','new'] and cp==103, 'Include the lookback boundary and advance only forward.'
assert select_window([],100,5)==([],100), 'An empty batch must not reset the checkpoint.'
selected[0]['id']='changed';assert rows[1]['id']=='late', 'Do not mutate input records.'
try: select_window([],0,-1)
except ValueError: pass
else: raise AssertionError('Reject negative lookback.')''',
  "print(select_window([{'ts':95},{'ts':103}], 100, 5))",'Select >= checkpoint-lookback, then take max with the previous checkpoint.')
q(c,'idempotency','Replay without duplicate revenue','An event stream is delivered at least once and may replay older versions.',
  'At-least-once delivery requires stable keys and version-aware upserts. A replayed old row must not overwrite newer state. Define tie handling explicitly and copy the current state so a caller can compare before and after.',
  'Implement merge_versions(current, incoming). current maps event IDs to dicts with id, version (int), amount. Incoming is a list with the same fields. Keep the highest version per id across both; equal versions retain the existing record (first seen wins). Return a new dict with copied records. Do not mutate either input.',
  'def merge_versions(current, incoming)',
  '''def merge_versions(current, incoming):
    out={k:dict(v) for k,v in current.items()}
    for row in incoming:
        key=row['id']
        if key not in out or row['version']>out[key]['version']: out[key]=dict(row)
    return out''',
  '''current={'a':{'id':'a','version':2,'amount':7}};incoming=[{'id':'a','version':1,'amount':99},{'id':'b','version':1,'amount':3}];result=merge_versions(current,incoming)
assert result['a']['amount']==7 and result['b']['amount']==3, 'Do not overwrite newer state with stale events.'
assert merge_versions(result,incoming)==result, 'Replaying the same batch must be idempotent.'
assert merge_versions(current,[{'id':'a','version':2,'amount':100}])['a']['amount']==7, 'Retain existing records on equal versions.'
result['a']['amount']=0;assert current['a']['amount']==7, 'Return independent dictionaries.' ''',
  "print(merge_versions({}, [{'id':'a','version':1,'amount':7}]))",'Copy the state first, then replace only when incoming version is strictly larger.')
q(c,'chunks','Aggregate a file without loading it all','A transaction export arrives as a generator of row batches.',
  'Chunking bounds memory but does not change aggregation semantics. Carry a small dictionary of partial sums across chunks. This works for associative operations such as sums; medians and distinct counts need more care.',
  'Implement aggregate_chunks(chunks). chunks is a one-pass iterable of row iterables. Each row has region and amount in integer paise, possibly negative. Return a dict of region -> total paise across all chunks, including regions totaling zero. Do not materialize all rows or mutate them.',
  'def aggregate_chunks(chunks)',
  '''def aggregate_chunks(chunks):
    totals={}
    for chunk in chunks:
        for row in chunk:
            key=row['region'];totals[key]=totals.get(key,0)+row['amount']
    return totals''',
  '''chunks=iter([iter([{'region':'N','amount':10}]),iter([]),iter([{'region':'N','amount':-10},{'region':'S','amount':7}])])
assert aggregate_chunks(chunks)=={'N':0,'S':7}, 'Combine chunks without dropping zero-sum groups.'
assert aggregate_chunks(iter([]))=={}, 'An empty stream has no groups.'
rows=[{'region':'X','amount':3}];assert aggregate_chunks([rows,rows])=={'X':6} and rows[0]['amount']==3, 'Accumulate independently of batch boundaries without mutation.' ''',
  "print(aggregate_chunks([[{'region':'N','amount':10}], [{'region':'N','amount':-2}]]))",'Keep only region totals in memory while iterating over chunks and rows.')
q(c,'redact','Logs without credentials','An incident report needs nested request metadata but must not expose secrets.',
  'Logging is a data egress path. Redaction needs to traverse nested structures and compare keys case-insensitively. This key-based exercise is deliberately limited: real systems also need allowlists, value-based detection, and controls on raw payload logging.',
  'Implement redact(value). Recursively copy dictionaries and lists. Replace values of dictionary keys token,password,api_key,authorization (case-insensitive strings) with ***. Leave other scalar values unchanged. Do not mutate the input.',
  'def redact(value)',
  '''def redact(value):
    secrets={'token','password','api_key','authorization'}
    if isinstance(value,dict): return {k:'***' if isinstance(k,str) and k.lower() in secrets else redact(v) for k,v in value.items()}
    if isinstance(value,list): return [redact(v) for v in value]
    return value''',
  '''source={'Token':'secret','request':[{'Authorization':'Bearer x','count':2}],'ok':True};out=redact(source)
assert out=={'Token':'***','request':[{'Authorization':'***','count':2}],'ok':True}, 'Redact nested dictionaries and lists case-insensitively.'
assert source['Token']=='secret' and source['request'][0]['Authorization']=='Bearer x', 'Do not mutate the original request.'
assert redact([None,3,{'api_key':None}])==[None,3,{'api_key':'***'}], 'Preserve scalars and redact even null secret fields.' ''',
  "print(redact({'token':'hidden','nested':[{'password':'hidden','ok':1}]}))",'Recursively handle dicts and lists, checking secret keys before traversing their values.')
q(c,'quality','Project: a pipeline release gate','A scheduled batch should fail its quality gate when duplicates or missing amounts cross the agreed thresholds.',
  'A quality gate turns expectations into measurable checks. Track the numerator and denominator, establish exact threshold behavior, and treat an empty batch deliberately. A passing gate does not prove correctness; business reconciliation and source freshness remain separate concerns.',
  'Implement quality_gate(rows, max_missing_fraction). Rows contain id and amount (number or None). Return a dict with row_count,duplicate_count,missing_fraction,passed. duplicate_count is rows minus distinct ids; missing_fraction is missing amount rows / rows (0.0 for empty). passed requires at least one row, zero duplicate_count, and missing_fraction <= threshold.',
  'def quality_gate(rows, max_missing_fraction)',
  '''def quality_gate(rows, max_missing_fraction):
    n=len(rows);duplicates=n-len({r['id'] for r in rows})
    missing=sum(r['amount'] is None for r in rows)/n if n else 0.
    return dict(row_count=n,duplicate_count=duplicates,missing_fraction=missing,passed=bool(n and duplicates==0 and missing<=max_missing_fraction))''',
  '''r=quality_gate([{'id':1,'amount':None},{'id':2,'amount':0}],.5)
assert r=={'row_count':2,'duplicate_count':0,'missing_fraction':.5,'passed':True}, 'An exact threshold passes; zero is not missing.'
assert not quality_gate([{'id':1,'amount':1},{'id':1,'amount':2}],1)['passed'], 'Duplicate business keys fail the gate.'
assert quality_gate([],1)=={'row_count':0,'duplicate_count':0,'missing_fraction':0.,'passed':False}, 'An empty batch is not a successful release.' ''',
  "print(quality_gate([{'id':1,'amount':None},{'id':2,'amount':0}], .5))",'Calculate missingness and duplicate rates explicitly, then combine the release conditions.',project=True)

c=course('production-data','Production Data Problem Solving','Debug state, joins, time windows, and operational failures with explicit contracts.','Year 2–3','🛠️','#d8b0ec')
q(c,'defaults','The list that remembers yesterday','A helper unexpectedly includes records from a previous function call.',
  'Mutable default arguments are created once at function definition time. A shared list can leak state across requests or scheduled runs. Use None as the sentinel, allocate a fresh list, and decide whether supplied containers should be copied or mutated.',
  'Implement add_tag(tag, tags=None). Return a new list containing the existing tags followed by tag. Never mutate a provided list and never share state between calls without tags.',
  'def add_tag(tag, tags=None)',
  '''def add_tag(tag, tags=None):
    return ([] if tags is None else list(tags))+[tag]''',
  '''assert add_tag('a')==['a'] and add_tag('b')==['b'], 'Calls without tags must not share mutable state.'
base=['x'];out=add_tag('y',base);assert out==['x','y'] and base==['x'], 'Copy supplied lists rather than appending in place.'
out.append('z');assert add_tag('y',base)==['x','y'], 'Outputs must not leak into later calls.' ''',
  "print(add_tag('cleaned', ['raw']))  # ['raw', 'cleaned']",'Use None as the default and return a copied list plus the new value.')
q(c,'jsonlines','Stream a partially corrupt JSONL file','A log file contains blank lines, valid JSON objects, and malformed lines.',
  'JSON Lines allows one independent JSON value per line, making streaming and quarantine straightforward. Track physical line numbers, including blank lines. A generator should not consume the entire source before yielding its first accepted record.',
  'Implement json_objects(lines) as a generator of (line_number, object_or_None). Ignore blank lines. Parse each nonblank line; yield its dict when JSON is an object, or None for malformed JSON and non-object values. Line numbers are 1-based physical positions. Consume a one-pass source lazily.',
  'def json_objects(lines)',
  '''import json
def json_objects(lines):
    for number,line in enumerate(lines,1):
        if not line.strip(): continue
        try:
            value=json.loads(line)
            yield number,value if isinstance(value,dict) else None
        except json.JSONDecodeError:
            yield number,None''',
  '''assert list(json_objects(iter(['','{"id":1}','oops','[1]',' null '])))==[(2,{'id':1}),(3,None),(4,None),(5,None)], 'Preserve physical line numbers and quarantine nonobjects.'
assert list(json_objects([]))==[], 'An empty log yields nothing.'
def source():
    yield '{"a":1}'
    raise RuntimeError('Do not consume ahead')
assert next(json_objects(source()))==(1,{'a':1}), 'Yield lazily without materializing the source.' ''',
  "print(list(json_objects(['{\"id\":1}', 'bad', ''])))",'Enumerate lines, skip blank text, parse with json.loads, and yield immediately.')
q(c,'hashjoin','Replace a nested-loop lookup','A reconciliation job scans every customer for every order and becomes slow.',
  'A dictionary index changes a many-to-one lookup from roughly O(n*m) to O(n+m), using memory proportional to the dimension. Validate uniqueness before joining; an arbitrary overwrite can hide corrupt dimensions. A left join must retain unmatched rows.',
  'Implement hash_left_join(facts, dimension). Dimension rows have id and label; fact rows have dimension_id and value. Reject duplicate dimension IDs with ValueError. Return copied fact rows with label added, using None for unmatched IDs. Preserve fact order and do not mutate inputs.',
  'def hash_left_join(facts, dimension)',
  '''def hash_left_join(facts, dimension):
    index={}
    for row in dimension:
        if row['id'] in index: raise ValueError('duplicate dimension key')
        index[row['id']]=row['label']
    return [dict(row,label=index.get(row['dimension_id'])) for row in facts]''',
  '''facts=[{'dimension_id':1,'value':9},{'dimension_id':2,'value':4}];dim=[{'id':1,'label':'N'}];out=hash_left_join(facts,dim)
assert out==[{'dimension_id':1,'value':9,'label':'N'},{'dimension_id':2,'value':4,'label':None}], 'Keep unmatched facts without losing row order.'
assert 'label' not in facts[0] and hash_left_join([],dim)==[], 'Do not mutate facts and support empty input.'
try: hash_left_join(facts,dim+dim)
except ValueError: pass
else: raise AssertionError('Reject duplicate dimension keys.')''',
  "print(hash_left_join([{'dimension_id':1,'value':9}], [{'id':1,'label':'N'}]))",'Build and validate an id-to-label index, then scan facts once.')
q(c,'sessions','Sessionize activity with a precise boundary','Product analytics defines a new session after more than 30 minutes of inactivity.',
  'Window boundaries are part of the metric definition. Here a gap of exactly the threshold stays in the same session. Sort events per user, carry only previous time and current session number, and restore original positions if the caller expects row alignment.',
  'Implement session_ids(events, gap). events contains user and integer minute. Assign session numbers starting at 1 per user, after sorting by minute and original position. Start a new session only when the gap is strictly greater than gap. Return session numbers aligned with original input order. Raise ValueError for negative gap.',
  'def session_ids(events, gap)',
  '''def session_ids(events, gap):
    if gap<0: raise ValueError('negative gap')
    result=[0]*len(events);state={}
    for i,row in sorted(enumerate(events),key=lambda x:(x[1]['user'],x[1]['minute'],x[0])):
        user,t=row['user'],row['minute']
        previous,session=state.get(user,(t,1))
        if t-previous>gap: session+=1
        result[i]=session;state[user]=(t,session)
    return result''',
  '''events=[{'user':'a','minute':61},{'user':'b','minute':2},{'user':'a','minute':0},{'user':'a','minute':30}]
assert session_ids(events,30)==[2,1,1,1], 'Use per-user state and strict gap boundaries, restoring original order.'
assert session_ids([],30)==[] and session_ids([{'user':'a','minute':0},{'user':'a','minute':0}],0)==[1,1], 'Tied times stay in one session.'
try: session_ids([], -1)
except ValueError: pass
else: raise AssertionError('Reject negative gaps.')''',
  "print(session_ids([{'user':'a','minute':0},{'user':'a','minute':31}],30))  # [1, 2]",'Sort indexed events, keep (previous minute, session) by user, and write results by original index.')
q(c,'asof','Join the dimension as it was then','A customer changed plan after a purchase; historical revenue needs the plan at purchase time.',
  'A temporal join must avoid looking into the future. For each event, select the latest dimension version with effective time <= event time. Half-open validity intervals and explicit tie handling make historical reports reproducible.',
  'Implement plans_at_event(events, history). Events have customer_id, ts (integer). History rows have customer_id, effective_ts (integer), plan. Return a list of plan strings or None aligned with events, choosing latest effective_ts <= event ts. On equal effective_ts choose the later history row. Do not mutate either input.',
  'def plans_at_event(events, history)',
  '''from bisect import bisect_right
def plans_at_event(events, history):
    versions={}
    for i,row in enumerate(history): versions.setdefault(row['customer_id'],[]).append((row['effective_ts'],i,row['plan']))
    lookup={}
    for key,rows in versions.items():
        rows.sort();lookup[key]=([r[0] for r in rows],[r[2] for r in rows])
    out=[]
    for event in events:
        times,plans=lookup.get(event['customer_id'],([],[]))
        index=bisect_right(times,event['ts'])-1
        out.append(plans[index] if index>=0 else None)
    return out''',
  '''history=[{'customer_id':'a','effective_ts':10,'plan':'basic'},{'customer_id':'a','effective_ts':20,'plan':'pro'},{'customer_id':'a','effective_ts':20,'plan':'team'}]
events=[{'customer_id':'a','ts':9},{'customer_id':'a','ts':10},{'customer_id':'a','ts':25},{'customer_id':'x','ts':99}]
assert plans_at_event(events,history)==[None,'basic','team',None], 'Do not use future plans; resolve equal-time versions deterministically.'
assert plans_at_event([],history)==[] and plans_at_event(events,[])==[None]*4, 'Handle missing events and dimension history.'
assert history[0]['plan']=='basic' and events[0]['ts']==9, 'Do not mutate source history.' ''',
  "print(plans_at_event([{'customer_id':'a','ts':10}], [{'customer_id':'a','effective_ts':20,'plan':'pro'}]))  # [None]",'Index sorted version times by customer and use bisect_right to find the last nonfuture version.')
q(c,'freshness','Separate stale, empty, and future data','A monitor should explain why a source cannot be trusted before the morning report.',
  'Freshness checks require a trusted clock and explicit tolerances. Future timestamps are a different failure from old data. Keep the evaluator pure by receiving now as an argument, making incident cases deterministic in tests.',
  'Implement freshness(timestamps, now, max_age). Inputs are numeric seconds. Return empty for no timestamps; future if any timestamp > now; stale if now-max(timestamps) > max_age; otherwise fresh. A source exactly max_age old is fresh. Raise ValueError for negative max_age.',
  'def freshness(timestamps, now, max_age)',
  '''def freshness(timestamps, now, max_age):
    if max_age<0: raise ValueError('negative max age')
    if not timestamps: return 'empty'
    latest=max(timestamps)
    if latest>now: return 'future'
    return 'stale' if now-latest>max_age else 'fresh' ''',
  '''assert freshness([80,90],100,10)=='fresh' and freshness([89],100,10)=='stale', 'Define the freshness boundary precisely.'
assert freshness([],100,10)=='empty' and freshness([101],100,10)=='future', 'Do not combine empty/future data with stale data.'
try: freshness([],100,-1)
except ValueError: pass
else: raise AssertionError('Reject negative tolerances.')''',
  "print(freshness([80,90],100,10))  # fresh",'Validate tolerance first, then handle empty, future, and age in that order.')
q(c,'intervals','Find overlapping job windows','Two jobs should not claim the same processing interval for the same source.',
  'Use half-open intervals [start,end): adjacent windows do not overlap. A sweep through sorted windows can detect overlap while tracking the furthest end reached. Comparing only each interval to the immediately preceding end fails on nested windows.',
  'Implement has_overlap(windows). Each item is (start,end), numbers with start < end. Return True if any half-open intervals overlap. Adjacent windows do not overlap. Raise ValueError for zero-length or reversed intervals. Do not mutate input.',
  'def has_overlap(windows)',
  '''def has_overlap(windows):
    if any(start>=end for start,end in windows): raise ValueError('invalid interval')
    furthest=None
    for start,end in sorted(windows):
        if furthest is not None and start<furthest: return True
        furthest=end if furthest is None else max(furthest,end)
    return False''',
  '''assert has_overlap([(0,10),(2,3),(9,12)]) and not has_overlap([(0,2),(2,4)]), 'Nested ranges overlap; touching boundaries do not.'
assert not has_overlap([]) and not has_overlap([(0,1)]), 'Handle empty and single windows.'
try: has_overlap([(0,0)])
except ValueError: pass
else: raise AssertionError('Reject empty processing intervals.')''',
  'print(has_overlap([(0,2),(2,4)]))  # False','Validate all ranges before scanning sorted starts; use start < furthest_end.')
q(c,'checkpoint','Project: commit data before the checkpoint','A worker crashes after persisting data but before recording its checkpoint.',
  'Saving the checkpoint too early loses data on failure. Saving it after durable output may replay data after a crash, so the sink must be idempotent. This exercise models side-effect ordering with callbacks; it does not claim exactly-once distributed delivery.',
  'Implement process_batch(rows, checkpoint, write_rows, save_checkpoint). Rows contain ts. Call write_rows(rows) first, even for empty rows. Only if it succeeds, call save_checkpoint(max(checkpoint, row timestamps)). Return that new checkpoint. If either callback raises, propagate the error. Never save a checkpoint when writing fails. Do not mutate rows.',
  'def process_batch(rows, checkpoint, write_rows, save_checkpoint)',
  '''def process_batch(rows, checkpoint, write_rows, save_checkpoint):
    new=max([checkpoint]+[r['ts'] for r in rows])
    write_rows(rows)
    save_checkpoint(new)
    return new''',
  '''calls=[]
assert process_batch([{'ts':12}],10,lambda rows:calls.append(('write',rows)),lambda cp:calls.append(('checkpoint',cp)))==12 and [c[0] for c in calls]==['write','checkpoint'], 'Persist data before advancing the checkpoint.'
saved=[]
try: process_batch([{'ts':20}],10,lambda rows:(_ for _ in ()).throw(RuntimeError('disk full')),saved.append)
except RuntimeError: pass
else: raise AssertionError('Propagate write failures.')
assert saved==[], 'Never save a checkpoint after a failed write.'
assert process_batch([],10,lambda rows:None,lambda cp:None)==10, 'Keep the checkpoint on an empty batch.' ''',
  "print(process_batch([{'ts':12}],10,lambda rows:None,lambda cp:None))  # 12",'Compute the candidate max, write, then checkpoint—without swallowing callback failures.',project=True)

c=course('data-case-studies','Real-World Data Case Studies','Solve business cases with explicit grains, time boundaries, reconciliations, and failure policies.','Year 2–3','🏭','#e6ba87')
c['time']='8–12 hours'
q(c,'retail','Retail: revised orders and refunds','A retailer receives repeated event versions; revenue must reflect the latest business truth.',
  'Deduplication must precede aggregation. Summing all versions overstates revenue, while summing only paid events before resolving versions can retain an order that was later canceled. Refunds have their own event IDs and contribute a negative amount.',
  'Implement retail_revenue(events). Each event has id (string),version (int),region,status (paid,refunded,canceled),amount (nonnegative integer paise). Keep greatest version per id; ties keep the first seen. Sum paid amounts and subtract refunded amounts per region; canceled events contribute no group. Return a dict sorted by region, retaining zero totals for contributing groups. Do not mutate events.',
  'def retail_revenue(events)',
  '''def retail_revenue(events):
    latest={}
    for e in events:
        if e['id'] not in latest or e['version']>latest[e['id']]['version']: latest[e['id']]=e
    totals={}
    for e in latest.values():
        if e['status']=='canceled': continue
        key=e['region']; sign=1 if e['status']=='paid' else -1
        totals[key]=totals.get(key,0)+sign*e['amount']
    return dict(sorted(totals.items()))''',
  '''events=[{'id':'o1','version':1,'region':'N','status':'paid','amount':100},{'id':'o1','version':2,'region':'N','status':'canceled','amount':100},{'id':'o2','version':1,'region':'S','status':'paid','amount':80},{'id':'r1','version':1,'region':'S','status':'refunded','amount':20}]
assert retail_revenue(events)=={'S':60}, 'Resolve versions before filtering statuses and summing revenue.'
assert retail_revenue(events+events)=={'S':60} and len(events)==4, 'Replay must not inflate revenue or mutate source.'
assert retail_revenue([])=={} and retail_revenue([events[2],dict(events[2],amount=999)])=={'S':80}, 'Handle empty input and first-seen version ties.' ''',
  "print(retail_revenue([{'id':'o1','version':1,'region':'N','status':'paid','amount':100}]))",'First build the latest-version index; only then classify statuses and aggregate integer money.',project=True)
q(c,'attribution','Marketing: last eligible touch','A conversion has several prior visits, direct traffic, and clicks outside the attribution window.',
  'Attribution is a policy, not an objective truth. This case uses the last nondirect touch for the same user, within an inclusive lookback interval. Never attribute to a future touch. Deterministic ties matter when logs have coarse timestamp resolution.',
  'Implement attribute(conversions, touches, lookback). Conversions have user,ts; touches have user,ts,channel. For each conversion choose the latest nondirect touch with conversion.ts-lookback <= touch.ts <= conversion.ts. On tied timestamps choose the later input touch. Return channel strings aligned to conversions, or unattributed. Raise ValueError for negative lookback.',
  'def attribute(conversions, touches, lookback)',
  '''def attribute(conversions, touches, lookback):
    if lookback<0: raise ValueError('negative lookback')
    result=[]
    for c in conversions:
        candidates=[(t['ts'],i,t['channel']) for i,t in enumerate(touches) if t['user']==c['user'] and t['channel']!='direct' and c['ts']-lookback<=t['ts']<=c['ts']]
        result.append(max(candidates)[2] if candidates else 'unattributed')
    return result''',
  '''touches=[{'user':'a','ts':5,'channel':'email'},{'user':'a','ts':9,'channel':'direct'},{'user':'a','ts':5,'channel':'search'},{'user':'a','ts':11,'channel':'future'}]
assert attribute([{'user':'a','ts':10},{'user':'b','ts':10}],touches,5)==['search','unattributed'], 'Ignore direct/future touches and resolve tied eligible touches.'
assert attribute([{'user':'a','ts':10}],touches,4)==['unattributed'] and attribute([],touches,5)==[], 'Respect the lookback window and empty conversions.'
try: attribute([],[], -1)
except ValueError: pass
else: raise AssertionError('Reject negative lookback.')''',
  "print(attribute([{'user':'a','ts':10}],[{'user':'a','ts':8,'channel':'email'}],5))",'Filter by user, time, and channel, then rank by timestamp and original touch position. For larger data, replace the reference scan with a per-user time index.',project=True)
q(c,'mrr','Subscriptions: monthly recurring revenue','Finance asks for MRR at a historical instant across monthly and annual plans.',
  'MRR is a normalized recurring metric, not cash received. Include subscriptions active at the snapshot and use half-open active intervals [start,end). Convert annual recurring value to monthly units. Do not mix canceled-history rows with current state without defining validity.',
  'Implement mrr_at(subscriptions, ts). Each row has id, start (int), end (int or None), billing (monthly or annual), price_paise (nonnegative integer). IDs are unique; annual amounts are divisible by 12. Return integer MRR paise for start <= ts and (end is None or ts < end). Annual rows contribute price_paise // 12; monthly rows contribute full price.',
  'def mrr_at(subscriptions, ts)',
  '''def mrr_at(subscriptions, ts):
    return sum(s['price_paise']//12 if s['billing']=='annual' else s['price_paise'] for s in subscriptions if s['start']<=ts and (s['end'] is None or ts<s['end']))''',
  '''subs=[{'id':'a','start':0,'end':10,'billing':'monthly','price_paise':100},{'id':'b','start':5,'end':None,'billing':'annual','price_paise':2400}]
assert mrr_at(subs,5)==300 and mrr_at(subs,10)==200, 'Normalize annual plans and use half-open validity.'
assert mrr_at(subs,-1)==0 and mrr_at([],5)==0, 'Exclude future subscriptions and handle empty input.'
assert mrr_at(subs,0)==100 and subs[0]['price_paise']==100, 'Include the exact start without changing money amounts.' ''',
  "print(mrr_at([{'id':'a','start':0,'end':None,'billing':'annual','price_paise':2400}],5))  # 200",'Filter active rows at the requested timestamp, then normalize annual amounts.',project=True)
q(c,'inventory','Operations: inventory reconciliation','The warehouse and storefront disagree about available stock, and some SKUs exist on only one side.',
  'A reconciliation needs a full outer view, not an inner join that hides missing keys. Keep presence separate from quantity; a missing record is not automatically equivalent to recorded zero stock. Make deltas directional.',
  'Implement reconcile_stock(warehouse, store). Each input maps SKU strings to integer counts. Return a SKU-sorted list of dicts with sku,warehouse,store,delta,status. Missing side values and delta are None. For matched SKUs delta=store-warehouse and status is matched if zero else mismatch. Missing sides have status missing_store or missing_warehouse.',
  'def reconcile_stock(warehouse, store)',
  '''def reconcile_stock(warehouse, store):
    out=[]
    for sku in sorted(warehouse.keys() | store.keys()):
        w,s=warehouse.get(sku),store.get(sku)
        delta=s-w if sku in warehouse and sku in store else None
        status='missing_warehouse' if sku not in warehouse else 'missing_store' if sku not in store else 'matched' if delta==0 else 'mismatch'
        out.append(dict(sku=sku,warehouse=w,store=s,delta=delta,status=status))
    return out''',
  '''out=reconcile_stock({'A':0,'B':5,'C':2},{'A':0,'B':3,'D':1})
assert [(r['sku'],r['delta'],r['status']) for r in out]==[('A',0,'matched'),('B',-2,'mismatch'),('C',None,'missing_store'),('D',None,'missing_warehouse')], 'Preserve missing keys and use store minus warehouse.'
assert out[2]['store'] is None and out[3]['warehouse'] is None, 'Missing is not recorded zero.'
assert reconcile_stock({}, {})==[], 'Handle two empty systems.' ''',
  "print(reconcile_stock({'A':5},{'A':3,'B':0}))",'Iterate over the union of keys, retaining missing-side values as None.',project=True)
q(c,'settlement','Payments: partial settlement audit','One order may have several settlement rows, and the provider can replay the same settlement event.',
  'Reconcile at order grain only after deduplicating settlement IDs. Partial payments must be summed; a dictionary keyed directly by order would discard all but one. Keep excess settlements and unknown orders visible for investigation.',
  'Implement settlement_audit(orders, settlements). orders maps order_id -> expected integer paise. settlements is a list of dicts with settlement_id,order_id,amount_paise (signed integer). Duplicate settlement_id rows are identical and count once. Return order_id-sorted dicts with order_id,expected,settled,delta,status over the union of order keys; unknown orders have expected=None,delta=None,status=unknown_order. Known status is matched when settled==expected, otherwise mismatch; delta=settled-expected. No settlement means settled=0.',
  'def settlement_audit(orders, settlements)',
  '''def settlement_audit(orders, settlements):
    totals={};seen=set()
    for s in settlements:
        if s['settlement_id'] in seen: continue
        seen.add(s['settlement_id']);key=s['order_id']
        totals[key]=totals.get(key,0)+s['amount_paise']
    out=[]
    for key in sorted(orders.keys() | totals.keys()):
        expected=orders.get(key);settled=totals.get(key,0)
        delta=settled-expected if key in orders else None
        out.append(dict(order_id=key,expected=expected,settled=settled,delta=delta,status='unknown_order' if key not in orders else 'matched' if delta==0 else 'mismatch'))
    return out''',
  '''rows=[{'settlement_id':'s1','order_id':'a','amount_paise':60},{'settlement_id':'s2','order_id':'a','amount_paise':40},{'settlement_id':'s3','order_id':'x','amount_paise':5}]
result=settlement_audit({'a':100,'b':20},rows+[rows[0]])
assert [(r['order_id'],r['settled'],r['status']) for r in result]==[('a',100,'matched'),('b',0,'mismatch'),('x',5,'unknown_order')], 'Deduplicate settlement events, sum partials, and retain orphans.'
assert result[1]['delta']==-20 and result[2]['delta'] is None, 'Calculate directional deltas only for known orders.'
assert settlement_audit({},[])==[], 'Handle no orders or settlements.' ''',
  "print(settlement_audit({'a':100},[{'settlement_id':'s1','order_id':'a','amount_paise':60}]))",'Deduplicate by settlement_id, group by order_id, then perform a full-key reconciliation.',project=True)
q(c,'anomaly','Monitoring: do not train on the incident','A rolling anomaly detector accidentally includes the current spike in its own baseline.',
  'For online detection, only past observations are available. Use exactly the prior window, not a centered rolling window or a window including the current value. A constant baseline needs an explicit rule because its standard deviation is zero. This simple detector is a baseline, not a complete alerting policy.',
  'Implement anomaly_flags(values, window, threshold). Inputs are finite numbers in time order; window >= 2, threshold > 0. Return a boolean list, False until window prior observations exist. Thereafter flag abs(current-prior_mean) > threshold * prior_population_std. If prior std is zero, flag any value unequal to prior_mean. Raise ValueError for invalid window/threshold.',
  'def anomaly_flags(values, window, threshold)',
  '''import statistics
def anomaly_flags(values, window, threshold):
    if window<2 or threshold<=0: raise ValueError('invalid detector configuration')
    flags=[]
    for i,value in enumerate(values):
        if i<window: flags.append(False);continue
        history=values[i-window:i];mean=statistics.mean(history);std=statistics.pstdev(history)
        flags.append(value!=mean if std==0 else abs(value-mean)>threshold*std)
    return flags''',
  '''assert anomaly_flags([1,1,1,100],3,3)==[False,False,False,True], 'The incident must not influence its own baseline.'
assert anomaly_flags([1,1,1,1],2,3)==[False]*4 and anomaly_flags([],2,3)==[], 'Constant normal data and empty series should not alert.'
try: anomaly_flags([1],1,3)
except ValueError: pass
else: raise AssertionError('Reject invalid window size.')''',
  'print(anomaly_flags([1,1,1,100],3,3))  # [False, False, False, True]','Slice values[i-window:i], compute population std, and handle zero variation.',project=True)
q(c,'features','ML: point-in-time customer features','A churn model must see only purchases available before its prediction time.',
  'Point-in-time correctness is a data engineering property as much as a modeling concern. Use a half-open feature window so events at the prediction instant cannot leak into the past. Include customers with no history so training and serving have consistent schemas.',
  'Implement customer_features(customers, events, cutoff, lookback). customers is a unique list of IDs. Events have customer_id,ts (integer),amount_paise (integer). Include cutoff-lookback <= ts < cutoff. Return customer-sorted dicts with customer_id,purchase_count,total_paise,last_ts (None with no events). Ignore unknown customers. Raise ValueError for lookback < 0. Do not mutate inputs.',
  'def customer_features(customers, events, cutoff, lookback)',
  '''def customer_features(customers, events, cutoff, lookback):
    if lookback<0: raise ValueError('negative lookback')
    state={key:dict(customer_id=key,purchase_count=0,total_paise=0,last_ts=None) for key in customers}
    for e in events:
        if e['customer_id'] not in state or not cutoff-lookback<=e['ts']<cutoff: continue
        r=state[e['customer_id']];r['purchase_count']+=1;r['total_paise']+=e['amount_paise']
        r['last_ts']=e['ts'] if r['last_ts'] is None else max(r['last_ts'],e['ts'])
    return [state[key] for key in sorted(state)]''',
  '''events=[{'customer_id':'a','ts':90,'amount_paise':10},{'customer_id':'a','ts':99,'amount_paise':20},{'customer_id':'a','ts':100,'amount_paise':999},{'customer_id':'x','ts':95,'amount_paise':7}]
assert customer_features(['b','a'],events,100,10)==[{'customer_id':'a','purchase_count':2,'total_paise':30,'last_ts':99},{'customer_id':'b','purchase_count':0,'total_paise':0,'last_ts':None}], 'Use half-open history and retain customers with no events.'
assert customer_features(['a'],events,100,0)[0]['purchase_count']==0 and events[2]['amount_paise']==999, 'A zero-width window is empty; do not mutate source.'
try: customer_features([],[],0,-1)
except ValueError: pass
else: raise AssertionError('Reject negative lookback.')''',
  "print(customer_features(['a'],[{'customer_id':'a','ts':99,'amount_paise':20}],100,10))",'Initialize all customers, filter events before cutoff, then update counts, sums, and latest time.',project=True)
q(c,'final','Final case: a trustworthy regional data product','You own a daily revenue dataset and must explain accepted records, rejected rows, and replay behavior.',
  'A data product combines validation, version resolution, and business aggregation. Reject invalid records before they enter state, keep quarantine reasons deterministic, and aggregate at the correct grain. The contract below intentionally uses integer money and explicit tie rules so a reviewer can reproduce every result.',
  'Implement build_revenue_product(rows). A valid row has nonblank string id, nonnegative integer version (bool invalid), nonblank string region, and integer amount_paise (signed, bool invalid). Reject invalid rows as (input_index, reason), checking fields in order id,version,region,amount_paise. Among valid rows keep highest version per id; ties keep first. Return {accepted: number of surviving unique ids, rejected: list of rejected tuples, revenue: region-sorted dict summing surviving amount_paise}. Preserve region strings exactly. Never mutate rows.',
  'def build_revenue_product(rows)',
  '''def build_revenue_product(rows):
    latest={};rejected=[]
    for i,row in enumerate(rows):
        reason=None
        for key in ['id','version','region','amount_paise']:
            v=row.get(key)
            valid=(isinstance(v,str) and bool(v.strip())) if key in ('id','region') else (isinstance(v,int) and not isinstance(v,bool) and (v>=0 if key=='version' else True))
            if not valid: reason=key;break
        if reason: rejected.append((i,reason));continue
        if row['id'] not in latest or row['version']>latest[row['id']]['version']: latest[row['id']]=row
    totals={}
    for row in latest.values(): totals[row['region']]=totals.get(row['region'],0)+row['amount_paise']
    return dict(accepted=len(latest),rejected=rejected,revenue=dict(sorted(totals.items())))''',
  '''rows=[{'id':'a','version':1,'region':'N','amount_paise':10},{'id':'a','version':2,'region':'S','amount_paise':20},{'id':'b','version':0,'region':'S','amount_paise':-5},{'id':'','version':-1,'region':'N','amount_paise':7},{'id':'c','version':True,'region':'N','amount_paise':3}]
assert build_revenue_product(rows)=={'accepted':2,'rejected':[(3,'id'),(4,'version')],'revenue':{'S':15}}, 'Validate, resolve versions, then aggregate surviving records.'
assert build_revenue_product(rows[:3]+rows[:3])==build_revenue_product(rows[:3]), 'Replaying valid rows must not inflate revenue.'
assert build_revenue_product([])=={'accepted':0,'rejected':[],'revenue':{}}, 'Return a stable schema for an empty batch.'
assert build_revenue_product([dict(rows[0],amount_paise=True)])['rejected']==[(0,'amount_paise')] and rows[0]['amount_paise']==10, 'Reject bool money without mutating input.' ''',
  "print(build_revenue_product([{'id':'a','version':1,'region':'N','amount_paise':100}]))",'Validate in field priority, index survivors by stable id/version, then group integer amounts by region.',project=True)

def write():
    data=original+new
    (ROOT/'app/curriculum.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'Authored {len(data)} courses, {sum(len(c["lessons"]) for c in data)} exercises.')
if __name__ == '__main__': write()
