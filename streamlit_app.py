# Import python packages
import streamlit as st
import requests
from snowflake.snowpark.functions import col, when_matched

# App title
st.title(":cup_with_straw: Customize Your Smoothie! :cup_with_straw:")
st.write(
     """Choose the fruits you want in your custom Smoothie!
     """)

name_on_order = st.text_input('Name on Smoothie:')
st.write('The name on your Smoothie will be:', name_on_order)

cnx = st.connection("snowflake")
session = cnx.session()

# Editable orders table
my_dataframe = session.table("smoothies.public.orders") \
    .filter(col("ORDER_FILLED") == 0) \
    .collect()
editable_df = st.data_editor(my_dataframe)

submitted = st.button('Submit')
if submitted:
    if len(editable_df) == 0:
        st.warning("No unfilled orders to update.")
    else:
        og_dataset = session.table("smoothies.public.orders")
        edited_dataset = session.create_dataframe(editable_df)
        merge_result = og_dataset.merge(
            edited_dataset,
            (og_dataset['ORDER_UID'] == edited_dataset['ORDER_UID']),
            [when_matched().update({'ORDER_FILLED': edited_dataset['ORDER_FILLED']})]
        )
        st.success("Order status updated!", icon="👉")

# Ingredient selection
fruit_options_df = session.table("smoothies.public.fruit_options") \
    .select(col('FRUIT_NAME')) \
    .to_pandas()

ingredients_list = st.multiselect(
    'Choose up to 5 ingredients:',
    fruit_options_df['FRUIT_NAME'],
    max_selections=5
)

if ingredients_list:
    ingredients_string = ''

    for fruit_chosen in ingredients_list:
        ingredients_string += fruit_chosen + ' '
        st.subheader(fruit_chosen + ' Nutrition Information')
        smoothiefroot_response = requests.get(
            f"https://my.smoothiefroot.com/api/fruit/{fruit_chosen.lower()}"
        )
        if smoothiefroot_response.status_code == 200:
            sf_df = st.dataframe(data=smoothiefroot_response.json(), use_container_width=True)
        else:
            st.warning(f"Could not fetch nutrition info for {fruit_chosen}.")

    my_insert_stmt = """ insert into smoothies.public.orders(ingredients)
                    values ('""" + ingredients_string + """')"""
    st.write(my_insert_stmt)

    time_to_insert = st.button('Submit Order')
    if time_to_insert:
        session.sql(my_insert_stmt).collect()
        st.success('Your Smoothie is ordered!', icon="✅")
