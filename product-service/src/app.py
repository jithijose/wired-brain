from flask import Flask, jsonify, request
from db import db
import logging.config
import configparser
from sqlalchemy import exc
from Product import Product


logging.config.fileConfig("/config/logging.ini", disable_existing_loggers=False)
log = logging.getLogger(__name__)

def get_database_url():
    config = configparser.ConfigParser()
    config.read('/config/db.ini')
    database_configuration = config['mysql']
    host = database_configuration['host']
    username = database_configuration['username']
    #password = database_configuration['password']
    db_password = open('/run/secrets/db_password')
    password =  db_password.read()
    database = database_configuration['database']
    database_url = f'mysql://{username}:{password}@{host}/{database}'
    log.info(f'Connecting to database: {database_url}')
    return database_url


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = get_database_url()
db.init_app(app)


# List all products
@app.route('/products')
def get_products():
    log.debug('GET /products')
    try:
        products = [product.json for product in Product.find_all()]
        return jsonify(products)
    
    except exc.SQLAlchemyError:
        log.exception('An exception occured while retriving all products')
        return 'An exception occured while retriving all products', 500


#open one product
@app.route('/product/<int:id>')
def get_product(id):
    log.debug('GET /product/<int:id>')
    try:
        product = Product.find_by_id(id)
        if product:
            return jsonify(product.json)
        log.warning(f'GET /product/{id}: Product not found')
        return f'Product with id {id} not found', 404
    
    except exc.SQLAlchemyError:
        log.exception(f'An exception occurred while retrieving product {id}')
        return f'An exception occurred while retrieving product {id}', 500

#add new product
#curl --header "Content-Type:application/json" --request POST --data "{\"name\": \"Product 3\"}" http://localhost:5000/product
@app.route('/product', methods=['POST'])
def post_product():
    #retrive the product from the body
    request_product = request.json
    log.debug(f'POST /products with product: {request_product}')

    product = Product(None, request_product['name'])
    try:
        product.save_to_db()
        return jsonify(product.json), 201
    
    except exc.SQLAlchemyError:
        log.exception(f'An exception occurred while creating product with name: {product.name}')
        return f'An exception occurred while creating product with name: {product.name}', 500

    

#update existing product
@app.route('/product/<int:id>', methods=['PUT'])
def put_product(id):
    log.debug(f'PUT /product/{id}')
    try:
        existing_product = Product.find_by_id(id)

        if existing_product:
            updated_product = request.json

            existing_product.name = updated_product['name']
            existing_product.save_to_db()

            return jsonify(existing_product.json), 200

        log.warning(f'PUT /product/{id}: Existing product not found')
        return f'Product with id {id} not found', 404
    
    except exc.SQLAlchemyError:
        log.exception(f'An exception occurred while updating product with name: {updated_product.name}')
        return f'An exception occurred while updating product with name: {updated_product.name}', 500


#delete existing product
@app.route('/product/<int:id>', methods=['DELETE'])
def remove_product(id):
    log.debug(f'DELETE /product/{id}')
    try:
        existing_product = Product.find_by_id(id)

        if existing_product:
            existing_product.delete_from_db()

            return jsonify({
                'message': f'Product with id {id} deleted'
            }), 200

        log.warning(f'DELETE /product/{id}: Existing product not found')
        return f'Product with id {id} not found', 404
    
    except exc.SQLAlchemyError:
        log.exception(f'An exception occurred while deleting the product with id: {id}')
        return f'An exception occurred while deleting the product with id: {id}', 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')



