import zhong_yang.utils.tobacco_login as login
import zhong_yang.spiders.order_management as order_management

if __name__ == '__main__':
    tobacco_login = login.TobaccoLogin()
    cookies = tobacco_login.main_login("", "")
    order_management = order_management.OrderManagement(cookies)
    order_list = order_management.main()