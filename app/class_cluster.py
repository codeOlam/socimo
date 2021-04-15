import pandas as pd
import re
import spacy
import en_core_web_sm
from nltk.tokenize import RegexpTokenizer, WhitespaceTokenizer
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
import string
from sklearn.cluster import KMeans
import numpy as np
import sklearn.metrics as metrics
from scipy.spatial import distance

from app import db
from app.models import Post, User
import app.setwords as sw


nlp = en_core_web_sm.load()
tokenizer = RegexpTokenizer(r'\w+')
lemmatizer = WordNetLemmatizer()
stop_word = set(stopwords.words('english'))
punctuate = list(string.punctuation)
stop_word.update(punctuate)
word_tokenizer = WhitespaceTokenizer() 


def post_to_df():
	"""
	This function will get post queries and convert to 
	pd dataframe
	"""
	# get queries of all post and store in pd_dataframe
	#Defining the query
	# post_query = db.session.query(Post).with_entities(Post.user_id, Post.content)
	post_query = qs = db.session.query(User.name, Post.content).join(User)
	print('Post Query\n',post_query)

	#getting all post entries
	post_qs = post_query.all()
	print('Post Query Set\n',post_qs)

	#Provide alternate col name and set index
	# posts_to_df = pd.DataFrame.from_records(post_qs, 
	# 									index='name', 
	# 									columns=['name','content'])
	posts_to_df = pd.DataFrame([(d.name, d.content) for d in post_qs], columns=['name', 'content'])
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
	df[text] = df[text].apply(lambda elem: re.sub(r"(@[A-Za-z0–9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)|^rt|http.+?",
			"",
			elem))
	print('df[text]\n', df[text])

	return df

post_df = clean_post(post_df, 'content')
post_clean_list = post_df.content.to_list()
print('\nCleaned Post to List: \n', post_clean_list, '\n')


def tidy_up(text):
	"""
	This function will Tokenize posts splitting string into list
	remove stop words and reduce words to their root form by lemmatization 
	"""
	final_text = []
	for i in word_tokenizer.tokenize(text):
		if i.lower() not in stop_word:
			word = lemmatizer.lemmatize(i)
			final_text.append(word.lower())

	return " ".join(final_text)

post_df.content =post_df.content.apply(tidy_up)


#Cleaning up setwords
health = tidy_up(sw.health_related_words)
politics = tidy_up(sw.politics_related_words)
security = tidy_up(sw.security_related_words)
economic = tidy_up(sw.economic_related_words)

#Dropping duplicates
words =  health.split()
health = " ".join(sorted(set(words), key=words.index))

words = politics.split()
politics = " ".join(sorted(set(words), key=words.index))

words = security.split()
security = " ".join(sorted(set(words), key=words.index))

words = economic.split()
economy = " ".join(sorted(set(words), key=words.index))



#Implementing Jaccard SImilarity
def jaccard_similarity(q, doc):
	intersect = set(q).intersection(set(doc))
	union = set(q).union(set(doc))

	# print('\nlen(intersect)/len(union)', len(intersect)/len(union), '\n')

	return len(intersect)/len(union)


#Implementing Similarity Score
def sim_scores(group, content):
	points = []
	for post in content:
		s = jaccard_similarity(group, post)
		points.append(s)

	# print('\nFrom sim_scores', points)
	return points

#Comparing Post contents using jaccard similarity and 
#Getting scores of all cluster points
h_points = sim_scores(health, post_df.content.to_list())
p_points = sim_scores(politics, post_df.content.to_list())
s_points = sim_scores(security, post_df.content.to_list())
e_points = sim_scores(economy, post_df.content.to_list())

#Creating a DF for Jaccard Scores
data = {'names': post_df.name.to_list(),
		'health_point':h_points,
		'politics_point':p_points,
		'security_point':s_points,
		'economic_point':e_points}

points_df = pd.DataFrame(data)
print('')
print('data\n',points_df)

#Assigining Categories based on Highest point
def fetch_cate(h1,h2,h3,h4):
	heal = []
	poli = []
	sec = []
	eco = []

	for a, b, c, d in zip(h1, h2, h3, h4):
		m = max(a, b, c, d)
		if m == a:
			heal.append(1)
		else:
			heal.append(0)
		if m == b:
			poli.append(1)
		else:
			poli.append(0)
		if m == c:
			sec.append(1)
		else:
			sec.append(0)
		if eco == d:
			eco.append(1)
		else:
			eco.append(0)

	return heal, poli, sec, eco

h1 = points_df.health_point.to_list()
h2 = points_df.politics_point.to_list()
h3 = points_df.security_point.to_list()
h4 = points_df.economic_point.to_list()

heal, poli, sec, eco = fetch_cate(h1, h2, h3, h4)

data = {'name': points_df.names.to_list(),
		'health':heal,
		'politics': poli,
		'security': sec,
		'economic': eco}


cate_df = pd.DataFrame(data)

print('\ncategory\n', cate_df, '\n')

#Grouping Post by user
u_group_df = cate_df.groupby(['name']).sum()
print('\n\t\t\tGrouping by user\n', u_group_df, '\n')

#Adding a new column Total to get sum of user post
u_group_df['total_post'] = u_group_df['health'] + u_group_df['politics'] + \
					u_group_df['security'] + u_group_df['economic']

print('\n\t\t\tDataFrame\n', u_group_df, '\n')


#Adding a new row to get total posts in df
u_group_df.loc["Total"] = u_group_df.sum()

print('\n\t\t\tFinished DataFrame\n', u_group_df, '\n')


#Implementing K-Mean Algorithm
def bic_cal(kmeans, Arr):
	"""
	Calculate the Bayesian information criterion
	"""
	centers = [kmeans.cluster_centers_]
	labels = kmeans.labels_

	#Cluster Numbers
	m = kmeans.n_clusters
	#Cluster size
	n = np.bincount(labels)
	#size of post dataset
	N, d = Arr.shape

	#Calculating variance for all clusters beforehand
	cal_var = (1.0 / (N - m) / d) * sum([sum(distance.cdist(Arr[np.where(labels == i)], [centers[0][i]], 'euclidean')**2) for i in range(m)])
	const_term = 0.5*m*np.log(N)*(d+1)

	BIC = np.sum([n[i]*np.log(n[i]) - n[i]*np.log(N) - ((n[i] * d) / 2) * np.log(2*np.pi*cal_var) - \
		((n[i] - 1) * d/ 2) for i in range(m)]) - const_term

	return (BIC)

print('\n\t\t***************K-MEAN Algorithm Implementation*******************')
n_clst = 4

kmeans = KMeans(n_clusters=n_clst, 
				init='k-means++', 
				random_state=0, 
				max_iter=100, 
				n_init=10,
				verbose=True)

# print("\nClustering sparse data with %s" % kmeans)

#Setting Data values for k-mean fitting
k_data = {'health':heal,
		'politics': poli,
		'security': sec,
		'economic': eco}

# print('k_data: ',k_data)

k_data_df = pd.DataFrame(k_data).values

# print('\n\t\tk_data_df\n', k_data_df)

kmeans.fit(k_data_df)

# print('\nkmeans.fit(k_data_df): ', kmeans.fit(k_data_df))

cluster_num = kmeans.predict(k_data_df)
print('\ncluster_num): ', cluster_num)

labels = kmeans.labels_
print('\nlabels: ', labels)

cluster_centres = kmeans.cluster_centers_
print('\ncluster_centres: ', cluster_centres)
labels_unique = np.unique(labels)
print('\nlabels_unique', labels_unique)

lenlb = len(labels_unique)
label_elem = np.zeros([lenlb])
print('\nlabel_elem: ', label_elem)


cluster_post_data = {'User_name': post_df["name"],
					# 'Post': post_df["content"],
					'Cluster_Num': cluster_num,
					'Cleaned_Post': post_clean_list,
					'health':heal,
					'politics': poli,
					'security': sec,
					'economic': eco
					}

# print('\ncluster_post_data: \n', cluster_post_data)

#set to df
cluster_post_df = pd.DataFrame(cluster_post_data)
print('\nCluster in DF\n',cluster_post_df)


#Grouping Cluster by number
cluster_gp = cluster_post_df.groupby('User_name').sum()
print('\n\t\t**************Grouping Cluster By Number*******************\n', cluster_gp)

#getting users with post on security
sec_post_data = {'User_name': post_df.name.to_list(),
				'Cleaned_Post': post_clean_list,
				'Cluster_num': cluster_num,
				'security': sec,}
sec_post_df = pd.DataFrame(sec_post_data)
print('\nCluster in DF\n',cluster_post_df)

sec_cluster_group = sec_post_df.groupby('User_name', 'Cleaned_Post').sum()
print('\n\t\t**************sec_cluster_group*******************\n', sec_cluster_group)

elem_cluster = np.bincount(labels)
print('\nElement Cluster\n', elem_cluster)

for i in labels_unique:
	label_elem[i]=0

	for l in labels:
		if l == i:
			label_elem[i] +=1
	# print('Label = ', i, ' Number of Elements = ', label_elem[i])

num_post = len(post_df.content)
# print('\nNumber of Posts: ', num_post)

samp_size = min(num_post, 10)

# print('\nSample Size: ',samp_size)

silh_score = metrics.silhouette_score(k_data_df, labels, 
									metric='euclidean', 
									sample_size=samp_size)

# print("\nSilhouette score = ", round(silh_score, 3), "  for Sample Size = ", samp_size)


cluster_arry = np.asmatrix(k_data_df)

# print('\ncluster array\n', cluster_arry)

BIC = bic_cal(kmeans, cluster_arry)

# print('\nBayesian Information criterion score: ', BIC)