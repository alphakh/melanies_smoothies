# Import python packages
import streamlit as st
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
    og_dataset = session.table("smoothies.public.orders")
    edited_dataset = session.create_dataframe(editable_df)

    merge_result = og_dataset.merge(
        edited_dataset,
        (og_dataset['ORDER_UID'] == edited_dataset['ORDER_UID']),
        [when_matched().update({'ORDER_FILLED': edited_dataset['ORDER_FILLED']})]
    )

    st.write(merge_result)
    st.success("Someone clicked the button.", icon="👉")

# Ingredient selection
my_dataframe = session.table("smoothies.public.fruit_options").select(col('FRUIT_NAME'))

ingredients_list = st.multiselect(
    'choose up to 5 ingredients:'
    , my_dataframe
    ,max_selections=5
   )


if ingredients_list:
    ingredients_string = ''
     
    for fruit_chosen in ingredients_list:
        ingredients_string += fruit_chosen + ' '
        st.subheader(fruit_chosen + 'Nutrition_Information')
        smoothiefroot_response = requests.get("https://my.smoothiefroot.com/api/fruit/watermelon")
        sf_df = st.dataframe(data=smoothiefroot_response.json(), use_container_width=True)

    my_insert_stmt = """ insert into smoothies.public.orders(ingredients)
                    values ('""" + ingredients_string + """')"""
    st.write(my_insert_stmt)

    time_to_insert = st.button('Submit Order')
    if time_to_insert:
        session.sql(my_insert_stmt).collect()
        st.success('Your Smoothie is ordered!', icon="✅")
