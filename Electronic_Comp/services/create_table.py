import logging
import boto3
from botocore.exceptions import ClientError
from decimal import Decimal

class DynamoDBDemo:
    
    
    def create_table(self, table_name, key_schema, attribute_definitions, provisioned_throughput, region):
        
        try:
            dynamodb_resource = boto3.resource("dynamodb", region_name = "us-east-1")
            self.table = dynamodb_resource.create_table(TableName=table_name, KeySchema=key_schema, AttributeDefinitions=attribute_definitions,
                ProvisionedThroughput=provisioned_throughput)

            # Wait until the table exists.
            self.table.meta.client.get_waiter('table_exists').wait(TableName = table_name)
            
        except ClientError as e:
            logging.error(e)
            return False
        return True
        

    def store_an_item(self, region, table_name, item):
        try:
            dynamodb_resource = boto3.resource("dynamodb", region_name = "us-east-1")
            table = dynamodb_resource.Table(table_name)
            table.put_item(Item=item)
        
        except ClientError as e:
            logging.error(e)
            return False
        return True
        
        
     
    def get_an_item(self,region, table_name, key):
        try:
            dynamodb_resource = boto3.resource("dynamodb", region_name = "us-east-1")
            table = dynamodb_resource.Table(table_name)
            response = table.get_item(Key=key)
            item = response['Item']
            print(item)
        
        except ClientError as e:
            logging.error(e)
            return False
        return True
            
 

def main():
   
    region = None
    d = DynamoDBDemo()
    
    table_name = "ElectronicItem"
    
    key_schema=[
        {
            "AttributeName": "category",
            "KeyType": "HASH"
        },
        {
            'AttributeName': 'productid',
            'KeyType': 'RANGE'
        }
    ]
    
    attribute_definitions=[
        {
            "AttributeName": "category",
            "AttributeType": "S"
        },
        {
            "AttributeName": "productid",
            "AttributeType": "S"
        }
        
    ]
    provisioned_throughput={
        "ReadCapacityUnits": 1,
        "WriteCapacityUnits": 1
    }
    
    d.create_table(table_name, key_schema, attribute_definitions,provisioned_throughput, region)
    
    
    
    item = {
    	"category" : "mobile",
    	"productid" : "IPHO_001",
        "name" : "iPhone 17",
        "brand" : "Apple",
        "model" : "iPhone 17 pro max",
        "price" : Decimal('1299.99'),
    	"specscoreoutof100" : 79,
    	"warranty" : "1 year",
    	"weightkg" : Decimal('0.233'),
    	"features" : {
    	    "Processor" : "A19 Bionic",
            "RAM" : "12GB",
            "Storage" : "512GB",
            "Battery" : "4500mAh",
            "Camera" : "Triple 48MP",
            "Display" : "Super Retina XDR OLED",
            "OS" : "iOS 19",
            "Face ID" : "Yes",
            "USB-C" : "Yes",
            "Refresh Rate" : "120Hz"
	    }
    }
    
    d.store_an_item(region, table_name, item)
    
    
    item = {
        'category': 'laptop',
        'productid': 'LAPHP_003',
        'name': 'HP Spectre x360 14',
        'brand': 'HP',
        'model': 'Spectre x360 14-ef2013dx',
        'price': Decimal('1399.99'),
        'warranty': '2 years',
        'weightkg': Decimal('1.36'),
        'specscoreoutof100': 93,
        'features': {
            'Display': '13.5" 3K2K OLED Touchscreen',
            'Processor': 'Intel Core i7-1355U',
            'RAM': '16GB LPDDR4x',
            'Storage': '1TB PCIe NVMe SSD',
            'Graphics': 'Intel Iris Xe',
            'Battery Life': 'Up to 15 hours',
            'Operating System': 'Windows 11 Home',
            'Build': 'Aluminum chassis, 360° hinge',
            'Keyboard': 'Backlit, fingerprint reader',
            'Ports': '2x Thunderbolt 4, 1x USB-A, microSD',
            'Audio': 'Bang & Olufsen quad speakers',
            'Webcam': '5MP IR camera with privacy shutter',
            'Connectivity': 'Wi-Fi 6E, Bluetooth 5.3',
            'Security': 'Facial recognition, TPM 2.0',
            'Color': 'Nightfall Black'
        }
    }
    d.store_an_item(region, table_name, item)


    item = {
        'category': 'tv',
        'productid': 'TVSONY_003',
        'name': 'Sony Bravia XR A80L',
        'brand': 'Sony',
        'model': 'XR A80L',
        'price': Decimal('1799.00'),
        'warranty': '3 years',
        'weightkg': Decimal('18.5'),
        'specscoreoutof100': 92,
        'features': {
            'Screen Type': 'OLED',
            'Resolution': '4K UHD',
            'Smart Features': 'Google TV, Alexa Built-in',
            'Refresh Rate': '120Hz',
            'Ports': 'HDMI x4, USB x2'
        }
    }
    d.store_an_item(region, table_name, item)


    item = {
        'category': 'induction top',
        'productid': 'INDPHIL_005',
        'name': 'Philips Viva Collection',
        'brand': 'Philips',
        'model': 'HD4928/01',
        'price': Decimal('69.99'),
        'warranty': '1 year',
        'weightkg': Decimal('2.8'),
        'specscoreoutof100': 85,
        'features': {
            'Power': '2100W',
            'Control': 'Touch Panel',
            'Preset Menus': '6 Indian Recipes',
            'Body': 'Microcrystal Plate',
            'Timer': '0–3 hours'
        }
    }
    d.store_an_item(region, table_name, item)
    
    item = {
        'category': 'heaters',
        'productid': 'HEATBAJAJ_007',
        'name': 'Bajaj Majesty RX11',
        'brand': 'Bajaj',
        'model': 'RX11',
        'price': Decimal('49.99'),
        'warranty': '1 year',
        'weightkg': Decimal('3.2'),
        'specscoreoutof100': 88,
        'features': {
            'Type': 'Room Heater',
            'Heating Element': 'Quartz Tubes',
            'Safety': 'Tip-over switch, Thermal cut-off',
            'Power': '1000W',
            'Modes': 'Low/High Heat'
        }
    }
    d.store_an_item(region, table_name, item)


if __name__ == '__main__':
 main()