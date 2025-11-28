import boto3
import datetime
import requests
import re
import json 
import uuid
import jwt
from jwt.algorithms import RSAAlgorithm
from django.shortcuts import render, redirect,  get_object_or_404
from botocore.exceptions import ClientError
from django.http import HttpResponse
from boto3.dynamodb.conditions import Attr # helps to build a filter expression in dynamodb 
from .services.serpapi import normalize_products, fetch_google_shopping
from .services.SNS import notify_user_verified
from .services.create_bucket import delete_object
from boto3.dynamodb.conditions import Key
from decimal import Decimal
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from Electronic_Comp.s3_utils import get_presigned_image_url
from LibProduct.compare_products import ProductComparator


def compare_products(request):
    if request.method == "POST":
        product_ids = request.POST.getlist("product_ids")
        ids = [pid.split(":") for pid in product_ids]  # (category, productid)
        comparator = ProductComparator(product_ids=ids)
        rows = comparator.compare_features()
        
        # Mapping dictionary
        ATTRIBUTE_LABELS = {
            "brand": "Company",
            "model": "Version",
            "category": "Type",
            "name": "Product Name",
            "M" : "Features",
            "image_s3_key" : "Image Name",
            "price" : "Price",
            "productid" : "Product ID",
            "review" : "Reviews",
            "rating" : "Average Rating",
            "features": "Specifications",
            "specscoreoutof100" : "Spec Score",
            "warranty" : "Warranty",
            "weightkg" : "Weight (in kg)"
        }
    
        # ✅ Replace raw attribute names with friendly labels
        for row in rows:
            if row["attribute"] in ATTRIBUTE_LABELS:
                row["attribute"] = ATTRIBUTE_LABELS[row["attribute"]]
                
        
        return render(request, "compare.html", {
            "rows": rows,
            "products": comparator.products
        })

        
        
AWS_REGION = 'us-east-1'
USER_POOL_ID = 'us-east-1_wSOb7NGER'
CLIENT_ID = '4qeivq54fhf5dlki919mqnvvo1'
cognito = boto3.client("cognito-idp", region_name=settings.AWS_REGION)


# 1. SIGNUP - user enters: username, email, password
# ---------------------------
def signup_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect("signup")

        try:
            response = cognito.sign_up(
                ClientId=CLIENT_ID,
                Username=email,     # email used as login username
                Password=password,
                UserAttributes=[
                    {"Name": "email", "Value": email},
                    {"Name": "preferred_username", "Value": username},
                ],
            )
            messages.success(request, "Signup successful! Check your email for the verification code.")
            # Send user to verify page
            return redirect("verify", email=email)

        except cognito.exceptions.UsernameExistsException:
            messages.error(request, "User already exists.")
            return redirect("signup")

        except Exception as e:
            messages.error(request, f"Signup error: {e}")
            return redirect("signup")

    return render(request, "signup.html")  # show signup form


def verify_view(request, email):
    if request.method == "POST":
        code = request.POST.get("code")

        try:
            cognito.confirm_sign_up(
                ClientId=CLIENT_ID,
                Username=email,
                ConfirmationCode=code
            )
            notify_user_verified(email)
            
            messages.success(request, "Email verified successfully! You can now sign in.")
            return redirect("signin")

        except cognito.exceptions.CodeMismatchException:
            messages.error(request, "Incorrect verification code. Please try again.")
            return redirect("verify", email=email)

        except cognito.exceptions.ExpiredCodeException:
            messages.error(request, "Your code has expired. Click RESEND CODE to get a new one.")
            return redirect("verify", email=email)

        except Exception as e:
            messages.error(request, f"Verification failed: {e}")
            return redirect("verify", email=email)

    return render(request, "verify.html", {"email": email})


def resend_code_view(request, email):
    try:
        cognito.resend_confirmation_code(
            ClientId=CLIENT_ID,
            Username=email
        )
        messages.success(request, "A new verification code has been sent to your email.")
    except Exception as e:
        messages.error(request, f"Failed to resend code: {e}")

    return redirect("verify", email=email)

def signin_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        # 🔒 Hardcoded admin credentials
        ADMIN_EMAIL = "chaitalikadamaws@gmail.com"
        ADMIN_PASSWORD = "Admin@123"

        # Special case: hardcoded admin
        if email.lower() == ADMIN_EMAIL.lower() and password == ADMIN_PASSWORD:
            messages.success(request, "Login successful as Admin!")
            return render(request, "add_product.html")

        # Otherwise, authenticate with Cognito
        try:
            auth_response = cognito.initiate_auth(
                ClientId=CLIENT_ID,
                AuthFlow="USER_PASSWORD_AUTH",
                AuthParameters={
                    "USERNAME": email,
                    "PASSWORD": password
                },
            )

            id_token = auth_response["AuthenticationResult"]["IdToken"]
            access_token = auth_response["AuthenticationResult"]["AccessToken"]

            # Save tokens in session
            request.session["id_token"] = id_token
            request.session["access_token"] = access_token
            request.session["email"] = email

            # Normal user flow
            messages.success(request, "Login successful as User!")
            return redirect("display")

        except cognito.exceptions.NotAuthorizedException:
            messages.error(request, "Incorrect email or password.")
            return redirect("signin")

        except cognito.exceptions.UserNotConfirmedException:
            messages.error(request, "Email not verified. Please verify before logging in.")
            return redirect("verify", email=email)

        except cognito.exceptions.UserNotFoundException:
            messages.error(request, "No account found with that email. Please sign up first.")
            return redirect("signup")

        except Exception as e:
            messages.error(request, f"Login failed: {e}")
            return redirect("signin")

    return render(request, "signin.html")

    
def logout_view(request):
    request.session.flush()
    return redirect("signup")
    
def display_view(request):
    return render(request, "display.html")

def mobile_view(request):
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    table = dynamodb.Table("ElectronicItem")
    category = request.GET.get("category")

    # Scan DynamoDB for products
    if category:
        response = table.scan(FilterExpression=Attr("category").eq(category))
    else:
        response = table.scan()

    products = response.get("Items", [])

    # Attach competitor prices, pre-signed image URLs
    for product in products:
        query = product.get("name")
        if query:
            try:
                raw = fetch_google_shopping(query)
                product["competitor_prices"] = normalize_products(raw)
            except Exception as e:
                print(f"Error fetching competitor prices for {query}: {e}")
                product["competitor_prices"] = []
                product["error"] = str(e)

        product_id = product.get("productid")
        if product_id:
            product["image_url"] = get_presigned_image_url(product_id)

        # Reviews are already embedded in product["reviews"]
        # Ensure it's always a list so template loops safely
        if "reviews" not in product:
            product["reviews"] = []

    return render(request, "mobile.html", {
        "category": category if category else "All",
        "products": products,
    })



def serpapi_search_view(request, product_name):
    # Connect to DynamoDB
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    table = dynamodb.Table("ElectronicItem")

    # Look up product in DynamoDB
    response = table.scan(
        FilterExpression=Attr("name").eq(product_name)
    )
    items = response.get("Items", [])
    product = items[0] if items else None

    # If product not found, return error
    if not product:
        return render(request, "mobile.html", {
            "query": product_name,
            "products": [],
            "error": f"No product found in DynamoDB with name {product_name}",
        })

    # Build query string for external API
    query = f'"{product["name"]}"'

    try:
        # Fetch competitor products from Google Shopping (via SerpAPI wrapper)
        raw = fetch_google_shopping(query)
        competitor_prices_raw = normalize_products(raw)

        # Extract meaningful keywords from product name
        raw_name = product["name"].lower()
        keywords = [w for w in re.split(r"\W+", raw_name) if len(w) > 2]

        # Filter competitor results: require all keywords to appear in title
        competitor_prices = [
            item for item in competitor_prices_raw
            if all(keyword in item["title"].lower() for keyword in keywords)
        ]

        # Render results in template
        return render(request, "mobile.html", {
            "query": query,
            "products": [product],   # your product details
            "competitor_prices": competitor_prices,
        })

    except Exception as e:
        # Handle API errors gracefully
        return render(request, "mobile.html", {
            "query": query,
            "products": [product],
            "competitor_prices": [],
            "error": f"API error: {e}",
        })

def competitor_prices(request, productid):
    try:
        raw = fetch_google_shopping(productid)
        prices = normalize_products(raw)
        return render(request, "competitor_prices.html", {"prices": prices})
    except Exception as e:
        return render(request, "competitor_prices.html", {"error": str(e)})
        

def add_product_view(request):
    AWS_REGION = "us-east-1"
    BUCKET_NAME = "chaitalibucket1001"
    TABLE_NAME = "ElectronicItem"
    if request.method == "POST":
        category = request.POST.get("category")
        productid = request.POST.get("productid")
        name = request.POST.get("name")
        brand = request.POST.get("brand")
        model = request.POST.get("model")
        price = request.POST.get("price")
        warranty = request.POST.get("warranty")
        weightkg = request.POST.get("weightkg")
        specscore = request.POST.get("specscore")
        image_file = request.FILES.get("image")
        
        # parse features JSON if uploaded
        features = {}
        if "features_json" in request.FILES:
            try:
                features_file = request.FILES["features_json"]
                features = json.load(features_file)  # dict of key/value
            except Exception as e:
                messages.error(request, f"Invalid JSON file: {e}")
                return redirect("add_product")

        # S3 + DynamoDB clients
        s3 = boto3.client("s3", region_name=AWS_REGION)
        dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
        table = dynamodb.Table(TABLE_NAME)

        # Upload image first
        file_ext = image_file.name.split(".")[-1]
        s3_key = f"{productid}"

        try:
            s3.upload_fileobj(
                image_file.file,
                BUCKET_NAME,
                s3_key,
                ExtraArgs={"ContentType": image_file.content_type}
            )
        except Exception as e:
            messages.error(request, f"S3 Upload Error: {e}")
            return redirect("add_product")

        # Store record in DynamoDB
        item = {
            "category": category,
            "productid": productid,
            "name": name,
            "brand": brand,
            "model": model,
            "price": Decimal(price),
            "warranty": warranty,
            "weightkg": Decimal(weightkg),
            "specscoreoutof100": int(specscore),
            "features": features,
            "image_s3_key": s3_key
        }

        try:
            table.put_item(Item=item)
            messages.success(request, "Product saved successfully!")
        except Exception as e:
            messages.error(request, f"DynamoDB Error: {e}")

        return redirect("add_product")

    return render(request, "add_product.html")
    
def product_list_view(request):
    AWS_REGION = "us-east-1"
    BUCKET_NAME = "chaitalibucket1001"
    TABLE_NAME = "ElectronicItem"
    dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
    table = dynamodb.Table(TABLE_NAME)

    try:
        response = table.scan()
        items = response.get('Items', [])
    except Exception as e:
        messages.error(request, f"DynamoDB scan failed: {e}")
        items = []

    # Prepare simplified product list
    products = []
    for item in items:
        products.append({
            'category': item.get('category'), 
            'productid': item.get('productid'),
            'name': item.get('name'),
            'image_s3_key': item.get('image_s3_key', 'N/A'),
            'features': item.get('features', {})
        })

    return render(request, 'product_list.html', {'products': products})

def edit_product_view(request, category, productid):
    AWS_REGION = "us-east-1"
    BUCKET_NAME = "chaitalibucket1001"
    TABLE_NAME = "ElectronicItem"
    dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
    table = dynamodb.Table(TABLE_NAME)
    s3 = boto3.client("s3", region_name=AWS_REGION)

    # Fetch product
    try:
        resp = table.get_item(Key={'category': category, 'productid': productid})
        item = resp.get('Item')
        if not item:
            messages.error(request, "Product not found.")
            return redirect('product_list')
    except Exception as e:
        messages.error(request, f"Error fetching product: {e}")
        return redirect('product_list')

    if request.method == "POST":
        # Collect updated fields
        name = request.POST.get("name", item.get("name"))
        brand = request.POST.get("brand", item.get("brand"))
        model = request.POST.get("model", item.get("model"))
        price = request.POST.get("price", item.get("price"))
        warranty = request.POST.get("warranty", item.get("warranty"))
        weightkg = request.POST.get("weightkg", item.get("weightkg"))
        specscore = request.POST.get("specscore", item.get("specscoreoutof100"))

        # Optional features JSON upload
        features = item.get("features", {})
        if "features_json" in request.FILES:
            try:
                features_file = request.FILES["features_json"]
                features = json.load(features_file)
            except Exception as e:
                messages.error(request, f"Invalid features JSON: {e}")
                return redirect('edit_product', category=category, productid=productid)

        # Optional image upload
        image_file = request.FILES.get("image")
        image_s3_key = item.get("image_s3_key")
        if image_file:
            try:
                s3.upload_fileobj(
                    image_file.file,
                    BUCKET_NAME,
                    image_s3_key or f"{productid}",
                    ExtraArgs={"ContentType": image_file.content_type}
                )
                image_s3_key = image_s3_key or f"{productid}"
            except Exception as e:
                messages.error(request, f"S3 Upload Error: {e}")
                return redirect('edit_product', category=category, productid=productid)

        # Normalize numeric fields
        try:
            price = Decimal(str(price))
            weightkg = Decimal(str(weightkg))
            specscore = int(specscore)
        except Exception as e:
            messages.error(request, f"Invalid numeric fields: {e}")
            return redirect('edit_product', category=category, productid=productid)

        # Update item in DynamoDB
        try:
            table.update_item(
                Key={'category': category, 'productid': productid},
                UpdateExpression="""
                    SET #n=:name, brand=:brand, model=:model,
                        price=:price, warranty=:warranty,
                        weightkg=:weightkg, specscoreoutof100=:specscore,
                        features=:features, image_s3_key=:image_s3_key
                """,
                ExpressionAttributeNames={'#n': 'name'},
                ExpressionAttributeValues={
                    ':name': name,
                    ':brand': brand,
                    ':model': model,
                    ':price': price,
                    ':warranty': warranty,
                    ':weightkg': weightkg,
                    ':specscore': specscore,
                    ':features': features,
                    ':image_s3_key': image_s3_key
                }
            )
            messages.success(request, "Product updated successfully.")
        except Exception as e:
            messages.error(request, f"DynamoDB update failed: {e}")

        return redirect('product_list')

    # Pre-signed URL for preview
    image_url = None
    if item.get('image_s3_key'):
        try:
            image_url = s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': BUCKET_NAME, 'Key': item['image_s3_key']},
                ExpiresIn=3600
            )
        except Exception:
            image_url = None

    return render(request, 'edit_product.html', {'item': item, 'image_url': image_url})

def delete_product_view(request, category, productid):
    AWS_REGION = "us-east-1"
    BUCKET_NAME = "chaitalibucket1001"
    TABLE_NAME = "ElectronicItem"
    dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
    table = dynamodb.Table(TABLE_NAME)

    # Fetch product for confirmation
    try:
        resp = table.get_item(Key={'category': category, 'productid': productid})
        item = resp.get('Item')
        if not item:
            messages.error(request, "Product not found.")
            return redirect('product_list')
    except Exception as e:
        messages.error(request, f"Error fetching product: {e}")
        return redirect('product_list')

    if request.method == "POST":
        try:
            # Delete DynamoDB record
            table.delete_item(Key={'category': category, 'productid': productid})

            # Delete image from S3 if exists
            if item.get("image_s3_key"):
                try:
                    delete_object(AWS_REGION, BUCKET_NAME, item["image_s3_key"])
                except Exception as e:
                    messages.warning(request, f"Product deleted but image removal failed: {e}")

            messages.success(request, "Product deleted successfully.")
        except Exception as e:
            messages.error(request, f"Delete failed: {e}")

        return redirect('product_list')

    # Render confirmation page
    return render(request, 'delete_product.html', {'item': item})

def review_page(request):
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    table = dynamodb.Table("ElectronicItem")
    response = table.scan()
    items = response.get("Items", [])

    products = []
    for item in items:
        products.append({
            "category": item.get("category"),
            "productid": item.get("productid"),
            "name": item.get("name"),
            "features": item.get("features", {}),
            "reviews": item.get("reviews", [])
        })

    # Get Cognito ID token from session
    id_token = request.session.get("id_token")

    return render(request, "review.html", {
        "products": products,
        "id_token": id_token
    })

def add_review(request, category, productid):
    AWS_REGION = "us-east-1"
    TABLE_NAME = "ElectronicItem"
    USER_POOL_ID = "us-east-1_wSOb7NGER"  
    JWKS_URL = f"https://cognito-idp.us-east-1.amazonaws.com/us-east-1_wSOb7NGER/.well-known/jwks.json"
    jwks = requests.get(JWKS_URL).json()
    
    if request.method == "POST":
        rating = int(request.POST.get("rating"))
        review_text = request.POST.get("review_text")

        # Get Cognito ID token from hidden field
        id_token = request.session.get("id_token")
        userid, username = "anonymous", "guest"

        try:
            headers = jwt.get_unverified_header(id_token)
            kid = headers["kid"]
            key = next(k for k in jwks["keys"] if k["kid"] == kid)
            public_key = RSAAlgorithm.from_jwk(key)

            decoded = jwt.decode(
                id_token,
                public_key,
                algorithms=["RS256"],
                audience="4qeivq54fhf5dlki919mqnvvo1",  # <-- your Cognito App Client ID
                issuer=f"https://cognito-idp.us-east-1.amazonaws.com/us-east-1_wSOb7NGER"
            )
            userid = decoded.get("sub")  # Cognito unique user ID
            print("DEBUG id_token:", id_token)
            username = decoded.get("preferred_username") or decoded.get("email") or decoded.get("cognito:username")

        except Exception as e:
            print(f"JWT verification failed: {e}")

        new_review = {
            "userid": userid,
            "username": username,
            "rating": rating,
            "review": review_text,
            "created_at": datetime.datetime.utcnow().isoformat()
        }

        dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
        table = dynamodb.Table(TABLE_NAME)

        table.update_item(
            Key={"category": category, "productid": productid},
            UpdateExpression="SET reviews = list_append(if_not_exists(reviews, :empty), :r)",
            ExpressionAttributeValues={
                ":r": [new_review],
                ":empty": []
            }
        )

        messages.success(request, "Review added successfully!")

    return redirect("review_page")
    
    
def search_products(request):
    query = request.GET.get("q", "").lower()   # convert search term to lowercase
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    table = dynamodb.Table("ElectronicItem")
    response = table.scan()
    items = response.get("Items", [])

    results = []
    for item in items:
        name = item.get("name", "").lower()
        brand = item.get("brand", "").lower()
        model = item.get("model", "").lower()
        features = " ".join(item.get("features", {}).values()).lower()

        # ✅ check case-insensitive match
        if query in name or query in brand or query in model or query in features:
            results.append({
                "name": item.get("name"),
                "category": item.get("category"),
                "brand": item.get("brand"),
                "model": item.get("model"),
                "image_url": item.get("image_url", ""),
                "features": item.get("features", {})
            })

    return render(request, "search_products.html", {"results": results, "query": query})
    