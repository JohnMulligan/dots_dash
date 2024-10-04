import json
import pandas as pd
import requests
import plotly.express as px

from env import *

url=base_api_url+'physical-objects/'

results=[]
c=0
while url is not None:
# while c<1:
	r=requests.get(
		url
	)
	
	j=json.loads(r.text)
	
# 		print(j['next'])
	url=j['next']
	
	page_results=j['results']
	
	results+=page_results
	c+=1

top_level_keys=[
	'url',
	'id',
	'name',
	'internal_identifier',
	'archive_space_component_unique_identifier',
	'print_type',
	'status',
	'number_of_pages',
	'digitization_status',
	'created_at',
	'updated_at'
]

metadata_keys=[
	'url',
	'id',
	'post_digi_conservation_required',
	'clean_obj',
	'humidfy_obj',
	'relax_obj',
	'disbind_obj',
	'interleave_obj',
	'repairs_obj',
	'note',
	'created_at',
	'updated_at'
]

collection_keys=[
	'url',
	'id',
	'name',
	'unique_identifier',
	'description',
	'parent',
	'created_at',
	'updated_at'
]

processed_results=[]

for result in results:
	
	processed_result={}
	
	for top_level_key in top_level_keys:
		processed_result[top_level_key]=result[top_level_key]
	
	for metadata_key in metadata_keys:
		processed_result[f'METADATA__{metadata_key}']=result['metadata'][metadata_key]
	
	collection=next(iter(result['collections']),None)
	
	if collection is not None:
		for collection_key in collection_keys:
			processed_result[f'COLLECTION__{collection_key}']=collection[collection_key]
	else:
		for collection_key in collection_keys:
			processed_result[f'COLLECTION__{collection_key}']=None
	
	processed_results.append(processed_result)

def html_dump(df,filename):
	html_str=df.to_html()
	d=open(f'{filename}.html','w')
	d.write(html_str)
	d.close()
	
df = pd.DataFrame.from_records(processed_results)

df2=df.copy()

status_columns=df2[['digitization_status','status']]

consolidated_statuses=[]

for r in status_columns.itertuples():
	rdict=r._asdict()
	
# 	print(rdict['status'])
	
	if rdict['digitization_status']=='Not Digitized':
		if rdict['status']=='UNABLE_TO_DIGITIZE':
			consolidated_status='Requires Conservation'
		elif rdict['status']=='REGISTERED':
			consolidated_status='Registered'
		elif rdict['status']=='PREPARED_FOR_DIGITIZATION':
			consolidated_status='Prepared for digitization'
	else:
		consolidated_status=rdict['digitization_status']
	consolidated_statuses.append(consolidated_status)

df2['consolidated_statuses']=consolidated_statuses

# print(df2)
# print(df2['consolidated_statuses'].unique())

median_num_pages=df2['number_of_pages'].median()

df3=df2.rename(columns={"internal_identifier":"Count","consolidated_statuses":"Status","COLLECTION__name":"Collection Name"})

df4=df3[['Status','Count','Collection Name']]
df4=df4.groupby(['Collection Name','Status']).count()

df4=df4.reset_index()

sunburst = px.sunburst(df4,path=['Collection Name','Status'],values='Count')
sunburst.show()

html_dump(sunburst,'sunburst')


histogram=px.histogram(df4,x="Collection Name",y="Count",color="Status",barmode="stack",barnorm='percent')
histogram.show()

html_dump(histogram,'histogram')

df5=df3[['Status','Count']]

df6=df5.groupby('Status').count()
df6=df6.reset_index()
pie=px.pie(df6,names='Status',values='Count')
pie.show()
html_dump(pie,'pie')

df=df3.fillna(10)

df=df.rename(columns={"Count":"Name","number_of_pages":"Number of Pages"})

bar = px.bar(df,
	x="Collection Name",
	y="Number of Pages",
	color="Status",
	title="Digitization progress by collection",
	text="Name"
)
bar.show()

html_dump(bar,'bar')
