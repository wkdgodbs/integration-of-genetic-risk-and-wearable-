# integration-of-genetic-risk-and-wearable-
## predict and visualize risk of developing chronic diseases: integration of genetic risk and wearable data.

## Use Streamlit to present idea on a web application. streamlit.io

#!/usr/bin/env python
# coding: utf-8

#!pip install streamlit

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(
    page_title="Genetic Risk offset by Physical activity",
    layout="wide",
    initial_sidebar_state="expanded",
)
def matplotlib_charts(df, cols):
    plt.style.use("seaborn")
    # plt.style.use("seaborn-whitegrid")
    # plt.style.use("fivethirtyeight")
    # st.pyplot(df[cols].plot.area().get_figure())

    # st.pyplot(df[[
    #             "Remaining Population",
    #             "Cumulative Recovered Infections Estimate",
    #             "First Doses Administered",]
    #         ].plot.area().get_figure())

    plots = df[cols].plot.line(subplots=True)
    st.pyplot(plots[0].get_figure())

    # plots = df[cols].plot(
    #     subplots=True, layout=(2, 2)
    # )
    # st.pyplot(plots[0][0].get_figure())


if __name__ == "__main__":
    # st.info("Note: This is a demo web application")
    # todo global cols lists. One for cors and one for UI
    disease = [
        "Coronary Heart Disease",
        "Type II Diabetes",
        "Stroke",
        "Breast Cancer",
        "Colon Cancer",
    ]
    # cols.extend(
    #     [
    #         "retail_and_recreation_percent_change_from_baseline",
    #         "grocery_and_pharmacy_percent_change_from_baseline",
    #         "parks_percent_change_from_baseline",
    #         "transit_stations_percent_change_from_baseline",
    #         "workplaces_percent_change_from_baseline",
    #         "residential_percent_change_from_baseline",
    #     ]



    w, h, = (
        900,
        400,
    )
    #------------------------------#
    # Data processing & Cox ph regression fitting and predicting
    #------------------------------#
    # We will use data extracted from STATA for later but for now, let me use other dataset as an example of illustration
    # df = pd.read_csv("uk_biobank_survival.csv")[disease_name]

    from lifelines import CoxPHFitter
    from lifelines.datasets import load_rossi

    df = pd.DataFrame(load_rossi())
    df = df.rename(
        columns={'week': 'timetoevent', 'arrest': 'censor', 'fin': 'gender', 'age': 'age', 'race': 'smoking',
                 'wexp': 'healthydiet', 'mar': 'sedentarybehavior', 'paro': 'sleepingwell', 'prio': 'PA'})

    # Cox ph model Fitting
    cph = CoxPHFitter()
    cph.fit(df, duration_col='timetoevent', event_col='censor',
            formula="age + gender + smoking+ healthydiet + sedentarybehavior + sleepingwell + PA")

    #cph.print_summary()  # access the individual results using cph.summary



    with st.sidebar:
        st.title("User Selection")
        st.subheader("Select a disease type below:")
        disease_selection = st.radio(
            "Disease type",
            disease,
        )
        user_id = int(st.number_input("Your User ID: " ))
        age = st.slider("Select a number", 20, 80)
        st.write("Your age is", age)
        # sex (tick box)
        sex = st.radio("Select your sex",
        ('Male', 'Female'))
        st.write("Your sex is: ", sex)
        # body weight and height => BMI
        height = st.number_input("Provide your height(cm)", 1, 200)
        weight = st.number_input("Provide your weight(kg)", 1, 150)

    # https://docs.streamlit.io/en/stable/troubleshooting/caching_issues.html#how-to-fix-the-cached-object-mutated-warning


    if disease_selection == "Coronary Heart Disease":
        st.title("Coronary Heart Disease Risk Estimation")
        # df,cols= rename_columns(df)
        bmi = weight / ((height / 100) ** 2)
        st.write("Your BMI is: ", round(bmi, 2))
        # Regular excercise (selection box)
        PA_change = st.slider("Select how intense you exercise in a week", min_value=0, max_value=10)
        timepoint = st.slider('Risk at which timepoint do you want to look at compare to Now?', min_value=0, max_value=max(df.timetoevent),
                             value=(max(df.timetoevent)-min(df.timetoevent))-42,
                             step=10, format="%d months")
        cph.plot_partial_effects_on_outcome(covariates='PA', values=[0, 2, 4, 6, 8, 10], cmap='coolwarm')

        # Prediction
        user_id = user_id
        X = df.iloc[user_id:(user_id+1)]
        user_pred_survfn = cph.predict_survival_function(X)
        user_pred_median = cph.predict_median(X)
        user_pred_partialhazard = cph.predict_partial_hazard(X)

        PA_current = X.at[user_id, 'PA']
        st.write("Your current Physical Activity intensity level is: ", PA_current)
        user_survivalrate_pre = user_pred_survfn.iloc[timepoint]
        X.at[user_id, 'PA'] = PA_change
        user_pred_survfn_change = cph.predict_survival_function(X)
        user_survivalrate_post = user_pred_survfn_change.iloc[timepoint]
        percentage_change = 100*(user_survivalrate_pre - user_survivalrate_post)/user_survivalrate_pre
#-----------------------------------------------------------------#
# Show Risk (percentage) reduction result
#-----------------------------------------------------------------#
        #st.write("Your adjusted genetic risk of getting {}c is: ".format(disease_selection), RR)
        st.write("Reduced risk is {} %".format(percentage_change.values))
        import plotly.graph_objects as go

        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value= float(user_survivalrate_post),
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Hazard Rate & Reduced Risk of {}".format(disease_selection), 'font': {'size': 24}},
            delta={'reference': float(user_survivalrate_pre), 'increasing': {'color': "RebeccaPurple"}},
            gauge={
                'axis': {'range': [None, 1], 'tickwidth': 1, 'tickcolor': "darkblue"},
                'bar': {'color': "darkblue"},
                'bgcolor': "white",
                'borderwidth': 2,
                'bordercolor': "gray",
                'steps': [
                    {'range': [0, float(user_survivalrate_pre)], 'color': 'cyan'},
                    {'range': [float(user_survivalrate_pre), float(user_survivalrate_post)], 'color': 'royalblue'}],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 0.99}}))

        fig.update_layout(paper_bgcolor="lavender", font={'color': "darkblue", 'family': "Arial"})
        fig.update_traces(number_valueformat=".2%", selector = dict(type='indicator'))

        st.plotly_chart(fig)




        st.markdown(
            """ 
        ## Further Explanation
        """
        )
    st.markdown(
        "Individual genetic risk is calculated through Job Godino model with absolute risk obtained from Competing risk model as below"  )
    st.latex ("Yearly absolute risk = T2D incidence * OR * (1 -  NonT2D mortality)")
    st.markdown(
        "Hazard Rate is estimated by fitting a multivariable Cox proportional hazard model"
    )
    st.latex("Hazard Rate ~ Cox(Genetic Risk + PA level + Age + Gender + ...")

    st.markdown("Created by [Haeyoon JANG].")
    st.write(
        "Disclaimer: This site was made by a data scientist, not an expert."
    )




