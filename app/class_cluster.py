import pandas as pd
import re
from app import db
from app.models import Post


def post_to_df():
	"""
	This function will get post queries and convert to 
	pd dataframe
	"""
	# get queries of all post and store in pd_dataframe
	#Defining the query
	post_query = db.session.query(Post).with_entities(Post.user_id, Post.content)
	print('Post Query\n',post_query)

	#getting all post entries
	post_qs = post_query.all()
	print('Post Query Set\n',post_qs)

	#Provide alternate col name and set index
	posts_to_df = pd.DataFrame.from_records(post_qs, 
										index='user_id', 
										columns=['user_id', 'content'])
	print('Post DataFrame\n', posts_to_df)

	return posts_to_df


post_df = post_to_df()


def clean_post(df, text):
	"""
	This function will clean post, removing unnecessary characters
	That will affect classification and clustering.
	"""
	#Convert all case to lower case.
	df[text] = df[text].str.lower()
	print('post_df.lower()\n', df[text])
	
	#Remove all unnecessary characters
	df[text] = df[text].apply(lambda elem: 
			re.sub(r"(@[A-Za-z0–9]+)|([0-9A-Za-z \t])|(\w+:\/\/\S+)|^rt|http.+?",
			"",
			elem))

	return df

post_df = clean_post(post_df, 'content')

print('Cleaned Post\n', post_df.head())