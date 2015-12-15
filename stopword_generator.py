from urllib import request
from bs4 import BeautifulSoup
from nltk import word_tokenize
from nltk.probability import FreqDist
from urllib.parse import urljoin

base_url = 'http://192.168.56.101/cases/'
html = request.urlopen(base_url).read().decode('utf8')
soup = BeautifulSoup(html, 'lxml')
counter = 0
max_docs = 10000
threshold = 0.9
urls = []
all_words = []
common_words = []

for a in soup.find_all('a', href=True):
    #print("Found the URL:", a['href'])
    url = urljoin(base_url, a['href'])
    if url.find("cases") > -1:
        #print('Reading URL: ', url);
        html = request.urlopen(url).read().decode('utf8', 'ignore')
        raw = BeautifulSoup(html, 'lxml').get_text()
        # if bad page, should be ignored from total count
        if raw.find('was not found on this server') < 0:
            urls.append(url)
            counter += 1
            tokens = word_tokenize(raw)
            words = [w.lower() for w in tokens]
            all_words.extend(set(words))
            #to analyze individual document frequency distribution
            #fd = FreqDist(words)
        #else:
            #print('URL ', url, ' had invalid contents')
        if counter >= max_docs:
            break

fd = FreqDist(all_words)
for word, count in fd.items():
    if(count >= (counter*threshold)):
        print(word, ' - ' , count)
        common_words.append(word)
common_words = sorted(common_words)
print('Total Number of URLs:', len(urls))
print('Total Number of unique words:', len(all_words))
print('Words found in all documents:', len(common_words))
print('Common words found in', int(counter*threshold) , 'documents:' , common_words)
