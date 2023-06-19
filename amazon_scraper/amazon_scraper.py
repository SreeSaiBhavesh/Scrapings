from datetime import datetime 
import csv
import bs4
import requests
import concurrent.futures
from tqdm import tqdm


USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
REQUEST_HEADER = {
    'User-Agent': USER_AGENT,
    'Accept-Language': 'en-US, en;q=0.5',
}
NO_THREADS = 10

def get_page_html(url):
    res = requests.get(url,headers=REQUEST_HEADER)
    return res.content

def get_product_price(soup):
    main_price_span = soup.find('span',attrs={
        'class':'a-price a-text-price a-size-medium apexPriceToPay'
    })
    price_spans = main_price_span.findAll('span')
    for span in price_spans:
        price = span.text.strip().replace('$','').replace(',','') # strip to remove any leading spacings
        try:
            return float(price)
        except ValueError:
            print("Value Obtained for price could not be parsed")
            exit()

def get_product_title(soup):
    product_title = soup.find('span', id='productTitle')
    return product_title.text.strip()

def get_product_rating(soup):
    prod_ratings_div = soup.find('div', attrs={
        'id':'averageCustomerReviews'
    })
    prod_rating_section = prod_ratings_div.find('i', attrs={'class':'a-icon-star'})
    product_rating_span = prod_rating_section.find('span')
    try:
        rating = product_rating_span.text.strip().split()
        return float(rating[0])
    except ValueError:
        print("Value Obtained For Rating Could Not Be Parsed")
        exit()

def get_product_tech_details(soup):
    details = {}
    tech_details_section = soup.find('div', id='productOverview_feature_div')
    data_tables = tech_details_section.findAll(
        'table', class_='a-normal a-spacing-micro')
    for table in data_tables:
        table_rows = table.findAll('tr')
        for row in table_rows:
            row_key = row.find('td', attrs={'class':'a-span3'}).text.strip()
            row_value = row.find('td', attrs={'class':'a-span9'}).text.strip().replace('\u200e', '')
            details[row_key] = row_value
    return details

def extract_product_info(url, output):
    product_info = {}
    #print(f'Scraping URL: {url}')
    html = get_page_html(url)
    soup = bs4.BeautifulSoup(html, 'lxml') # lxml can parse xml and html files
    product_info['price'] = get_product_price(soup)
    product_info['title'] = get_product_title(soup)
    product_info['rating'] = get_product_rating(soup)
    product_info.update(get_product_tech_details(soup))
    output.append(product_info)

if(__name__ == "__main__"):
    products_data = []
    urls = []
    with open('amazon_products_urls.csv', newline='') as csvfile:
        urls = list(csv.reader(csvfile,delimiter=','))
        # for row in reader:
        #     url = row[0]
        #     products_data.append(extract_product_info(url))
    with concurrent.futures.ThreadPoolExecutor(max_workers=NO_THREADS) as executor:
        for worker_num in tqdm(range(0, len(urls))):
            executor.submit(extract_product_info, urls[worker_num][0], products_data)
    
    output_file_name = 'output-{}.csv'.format(datetime.today().strftime("%m-%d-%Y"))
    with open(output_file_name, 'w') as outputFile:
        writer = csv.writer(outputFile)
        writer.writerow(products_data[0].keys())
        for product in products_data:
            writer.writerow(product.values())

