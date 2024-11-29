# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter

import psycopg2
from psycopg2 import sql

import logging

class FullbookscraperPipeline:
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        # Strip whitespaces from string
        field_names = adapter.field_names()
        for field_name in field_names:
            if field_name != 'description':
                value = adapter.get(field_name)
                adapter[field_name] = value[0].strip()

        # Product Type --> Switch to lowercase
        lowercase_keys = ['product_type']
        for lowercase_key in lowercase_keys:
            value = adapter.get(lowercase_key)
            adapter[lowercase_key] = value.lower()

        # Price --> convert to float
        price_keys = ['price_excl_tax','price_incl_tax','tax','price']
        
        for price_key in price_keys:
            value = adapter.get(price_key)
            value = value.replace('£', '')
            adapter[price_key] = float(value)

        # Availability --> extract number of books in stock
        availability_string = adapter.get('availability')
        split_string_array = availability_string.split('(')
        if len(split_string_array) < 2:
            adapter['availability'] = 0
        else:
            availability_array = split_string_array[1].split(' ')
            adapter['availability'] = int(availability_array[0])

        # Reviews --> convert string to number
        num_reviews_string = adapter.get('num_reviews')
        adapter['num_reviews'] = int(num_reviews_string)

        # Stars --> convert text to number
        stars_string = adapter.get('stars')
        split_stars_array = stars_string.split(' ')
        stars_text_value = split_stars_array[1].lower()
        stars_mapping = {
                "zero": 0,
                "one": 1,
                "two": 2,
                "three": 3,
                "four": 4,
                "five": 5,
            }
        adapter['stars'] = stars_mapping.get(stars_text_value, 0)

        return item

class SaveToPSQLPipeline:

    def __init__(self):
        # Connect to your postgres DB
        try:
            self.conn = psycopg2.connect(
                dbname="books",  # your database name
                user="postgres",       # replace with your PostgreSQL username
                password="Janani@1997",  # replace with your password
                host="localhost",      # or your PostgreSQL server address
                port="5432"            # default PostgreSQL port
            )

            # Create a cursor object using a context manager (with statement)
            self.cursor = self.conn.cursor()

        except psycopg2.Error as e:
            logging.error(f"Database connection failed: {e}")
            raise

        # Create a table (Table for storing book data)
        create_table_query = '''
        CREATE TABLE IF NOT EXISTS books (
            id SERIAL PRIMARY KEY,
            title TEXT,
            url VARCHAR(255),
            price DECIMAL,
            price_excl_tax DECIMAL,
            price_incl_tax DECIMAL,
            product_type VARCHAR(255),
            tax DECIMAL,
            availability INTEGER,
            num_reviews INTEGER,
            stars INTEGER,
            description TEXT
        );
        '''

        self.cursor.execute(create_table_query)
        self.conn.commit()

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        # Insert data into the database
        insert_query = '''
        INSERT INTO books (
            title, url, price, price_excl_tax, price_incl_tax,
            product_type, tax, availability, num_reviews, stars, description
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        '''
        try:
            self.cursor.execute(insert_query, (
                adapter.get('title', 'Unknown'),
                adapter.get('url', ''),
                float(adapter.get('price', '0')),
                float(adapter.get('price_excl_tax', '0')),
                float(adapter.get('price_incl_tax', '0')),
                adapter.get('product_type', '').lower(),
                float(adapter.get('tax', '0')),
                int(adapter.get('availability', 0)),
                int(adapter.get('num_reviews', 0)),
                int(adapter.get('stars', 0)),
                adapter.get('description', '')
            ))
            self.conn.commit()
            logging.info(f"Inserted item: {adapter.get('title')}")
        except Exception as e:
            logging.error(f"Error inserting item: {e}")
            self.conn.rollback()

        return item

    def close_spider(self, spider):
        # Close the database connection
        self.conn.commit()
        self.cursor.close()
        self.conn.close()

