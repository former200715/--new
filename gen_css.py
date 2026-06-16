import os
css_path = "D:/Users/ABC/Desktop/hotel-booking-dark/app/static/css/style.css"
css = open("D:/Users/ABC/Desktop/hotel-booking-dark/app/static/css/style.css.new", "r").read()
with open(css_path, "w") as f2:
    f2.write(css)
print("Done:", len(css))
