from selenium import webdriver
 
options = webdriver.ChromeOptions()
options.add_argument('--ignore-certificate-errors')
options.add_argument('--headless')
 
driver = webdriver.Chrome('chromedriver.exe',chrome_options=options)
driver.set_window_size(1920, 1080)

#urls = <get the url list>
 
for u in urls:

  driver.get(u)
  driver.save_screenshot('shots/%s.png' % u.replace('://','__'))
 
driver.close()