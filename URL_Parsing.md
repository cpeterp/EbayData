# Ovieview of Ebay's search query options
*These are, as best I can tell, the relavent paremeters of Ebay's search query*

## Useful Parameters

* **_nkw**: *INPUT*
    * Search text
    * input d_type: string
    * encoding: single
    * ex: "macbook pro 2017"
    * optional: false
* **_udlo**: *INPUT*
    * Price min
    * input d_type: int
    * ex: 20
    * optional: true
* **_udhi**: *INPUT*
    * Price max
    * input d_type: int
    * ex: 1234
    * optional: true
* **RAM%20Size**: *INPUT*
    * The amount of RAM
    * input d_type: string
    * encoding: double
    * ex: "16%20GB"
    * optional: true
* **Processor**: *INPUT*
    * The processor name
    * input d_type: string
    * encoding: double
    * ex: "AMD%20Ryzen%207"
    * optional: true
* **Release%20Year**: *INPUT*
    * Release year of the device
    * input d_type: int
    * ex: 2022
    * optional: true
* **Operating%20System**: *INPUT*
    * Operating system of the device
    * input d_type: string
    * encoding: double
    * ex: "Windows 11 Pro", "Windows 10", "Windows 10 Pro"
    * optional: true
* **SSD%2520Capacity**: *INPUT*
    * SSD Capacity
    * input d_type: string
    * encoding: double
    * ex: 256%20GB
    * optional: true
* **Model**: *INPUT*
    * Item model
    * input d_type: string
    * encoding: double
    * ex: "Lenovo%20ThinkPad%20T14"
    * optional: true
* **_sacat**: 0
    * Category variable (0 is either All or Default - i.e. let ebay decide)
    * input d_type: int
    * optional: true
* **LH_Complete**: 1 
    * Completed listings
    * input d_type: int
    * optional: true
* **LH_Sold**: 1
    * Sold listings
    * input d_type: int
    * optional: true
* **LH_ItemCondition**: *INPUT*
    * Conditionon of the item
    * Accepts multpile values with pipe seperators
    * input d_type: str
    * optional: true
    * Possible Values:
        * 1000: New
        * 1500: Open Box
        * 2000: Certified Refurbished
        * 2010: Excellent Refurbished
        * 2020: Very Good Refurbished
        * 2030: Good Refurbished
        * 2500: Seller Refurbished
        * 3000: Used
        * Note: Likely many other values work, but these options seem to apply to consumer electronics
* **_ipg**: 240
    * Items per page
    * input d_type: int
    * optional: true
    * default: 240
* **_pgn**: *INPUT*
    * Page number
    * input d_type: int
    * optional: true
    
## Unused Parameters
*These are added to the URL in a browser,but I can't tell what they do. They are not needed to make a request, and can be omitted*
* **_fsrp**
    * Purpose unclear
    * default: 1
* **rt**
    * Purpose unclear
    * default: "nc"
* **_from**
    * Purpose unclear
    * default: "R40"
