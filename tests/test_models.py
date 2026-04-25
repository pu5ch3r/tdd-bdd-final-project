# Copyright 2016, 2023 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Test cases for Product Model

Test cases can be run with:
    nosetests
    coverage report -m

While debugging just these tests it's convenient to use this:
    nosetests --stop tests/test_models.py:TestProductModel

"""
import os
import logging
import unittest
from decimal import Decimal
from service.models import Product, Category, db, DataValidationError
from service import app
from tests.factories import ProductFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)


######################################################################
#  P R O D U C T   M O D E L   T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestProductModel(unittest.TestCase):
    """Test Cases for Product Model"""

    @classmethod
    def setUpClass(cls):
        """This runs once before the entire test suite"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        Product.init_db(app)

    @classmethod
    def tearDownClass(cls):
        """This runs once after the entire test suite"""
        db.session.close()

    def setUp(self):
        """This runs before each test"""
        db.session.query(Product).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################

    def test_create_a_product(self):
        """It should Create a product and assert that it exists"""
        product = Product(name="Fedora", description="A red hat", price=12.50, available=True, category=Category.CLOTHS)
        self.assertEqual(str(product), "<Product Fedora id=[None]>")
        self.assertTrue(product is not None)
        self.assertEqual(product.id, None)
        self.assertEqual(product.name, "Fedora")
        self.assertEqual(product.description, "A red hat")
        self.assertEqual(product.available, True)
        self.assertEqual(product.price, 12.50)
        self.assertEqual(product.category, Category.CLOTHS)

    def test_add_a_product(self):
        """It should Create a product and add it to the database"""
        products = Product.all()
        self.assertEqual(products, [])
        product = ProductFactory()
        product.id = None
        product.create()
        # Assert that it was assigned an id and shows up in the database
        self.assertIsNotNone(product.id)
        products = Product.all()
        self.assertEqual(len(products), 1)
        # Check that it matches the original product
        new_product = products[0]
        self.assertEqual(new_product.name, product.name)
        self.assertEqual(new_product.description, product.description)
        self.assertEqual(Decimal(new_product.price), product.price)
        self.assertEqual(new_product.available, product.available)
        self.assertEqual(new_product.category, product.category)

    #
    # ADD YOUR TEST CASES HERE
    #
    def test_read_a_product(self):
        """It should read the product"""
        product = ProductFactory()
        product.id = None
        app.logger.info("new product: {product}")
        product.create()
        self.assertIsNotNone(product.id)
        new_product = Product.find(product.id)
        self.assertEqual(new_product.name, product.name)
        self.assertEqual(new_product.description, product.description)
        self.assertEqual(new_product.price, product.price)
        self.assertEqual(new_product.available, product.available)
        self.assertEqual(new_product.category, product.category)

    def test_update_a_product(self):
        """It should update a product in the database"""
        product = ProductFactory()
        app.logger.info("update product: {product}")
        product.id = None
        product.create()
        app.logger.info("product created: {product}")
        self.assertIsNotNone(product.id)
        product.description = "New description"
        original_id = product.id

        product.id = None
        with self.assertRaises(DataValidationError):
            product.update()

        product.id = original_id
        product.update()
        self.assertEqual(original_id, product.id)
        self.assertEqual(product.description, "New description")

        all_products = Product.all()
        self.assertEqual(len(all_products), 1)
        self.assertEqual(all_products[0].id, original_id)
        self.assertEqual(all_products[0].description, "New description")

    def test_delete_a_product(self):
        """It should delete a product"""
        product = ProductFactory()
        # create new product in db and memorize id
        product.create()
        product_id = product.id

        all_products = Product.all()
        self.assertEqual(len(all_products), 1)

        # delete again
        product.delete()

        # check if the previous id is really gone
        product = Product.find(product_id)
        self.assertIsNone(product)

    def test_list_all_products(self):
        """It should list all products"""
        # empty db
        self.assertEqual(len(Product.all()), 0)
        # setup 5 products
        for _ in range(5):
            product = ProductFactory()
            product.create()
        # ensure 5 products in db
        self.assertEqual(len(Product.all()), 5)

    def test_find_by_name(self):
        """It should find a product by name"""
        # empty db
        self.assertEqual(len(Product.all()), 0)

        # setup 5 products
        product_list = ProductFactory.create_batch(5)
        for product in product_list:
            product.create()

        # check number of  occurrances for first product name
        product_name = product_list[0].name
        count = sum(1 for product in product_list if product.name == product_name)

        product_matches = Product.find_by_name(product_name)
        self.assertEqual(product_matches.count(), count)

        for prod in product_matches:
            self.assertEqual(prod.name, product_name)

    def test_find_by_availability(self):
        """It should find products by availability"""
        # empty db
        self.assertEqual(len(Product.all()), 0)

        product_list = ProductFactory.create_batch(10)
        for product in product_list:
            product.create()

        available = product_list[0].available
        count = sum(1 for product in product_list if product.available == available)

        product_matches = Product.find_by_availability(available=available)
        self.assertEqual(product_matches.count(), count)
        for product in product_matches:
            self.assertEqual(product.available, available)

    def test_find_by_category(self):
        """It should find products by category"""
        # empty db
        self.assertEqual(len(Product.all()), 0)

        product_list = ProductFactory.create_batch(10)
        for product in product_list:
            product.create()

        category = product_list[0].category
        count = sum(1 for product in product_list if product.category == category)
        product_matches = Product.find_by_category(category)
        self.assertEqual(product_matches.count(), count)
        for product in product_matches:
            self.assertEqual(product.category, category)

    def test_find_by_price(self):
        """It should find products by price"""
        # empty db
        self.assertEqual(len(Product.all()), 0)

        product_list = ProductFactory.create_batch(10)
        for product in product_list:
            product.create()

        # Use a Decimal as price parameter
        price = product_list[0].price
        count = sum(1 for product in product_list if product.price == price)
        product_matches = Product.find_by_price(price)
        self.assertEqual(product_matches.count(), count)
        for product in product_matches:
            self.assertEqual(product.price, price)

        # Use a string as price parameter
        product_matches = Product.find_by_price(str(price))
        self.assertEqual(product_matches.count(), count)

    def test_serialize_product(self):
        """It should serialize a product to a dictionary"""

    def test_deserialize_product_exceptions(self):
        """It should catch exceptions when deserialize a product from a dictionary"""
        # empty db
        self.assertEqual(len(Product.all()), 0)

        product_dict = {
            "name": "Foo",
            "description": "Baz Bar",
            "price": "567.89",
            "available": "True",
            "category": "CLOTHS"
        }
        product = Product()
        with self.assertRaises(DataValidationError):
            product.deserialize(data=product_dict)

        product_dict = {
            "name": "Waldo Bar",
            "description": "Fred Bar",
            "price": "1111.99",
            "available": "FALSE",
            "category": "AUTOMOTIVE"
        }

        product = Product()
        with self.assertRaises(DataValidationError):
            product.deserialize(data=product_dict)

        product_dict = {
            "name": None,
            "description": "",
            "pritzel": False,
            "available": None,
            "category": "OTHER"
        }

        product = Product()
        with self.assertRaises(DataValidationError):
            product.deserialize(data=product_dict)

    def test_deserialize_product(self):
        """It should deserialize a product from a dictionary"""
        # empty db
        self.assertEqual(len(Product.all()), 0)

        product_dict = {
            "name": "Foobar",
            "description": "Fred",
            "price": "1111.99",
            "available": False,
            "category": "FOOD"
        }
        product = Product()

        product.deserialize(data=product_dict)
        product.create()

        self.assertEqual(product.name, product_dict["name"])
        self.assertEqual(product.description, product_dict["description"])
