// =====================================================
// USER DASHBOARD JAVASCRIPT
// =====================================================


document.addEventListener(
    "DOMContentLoaded",
    function () {

        loadUserSummary();

        loadDemandChart();

    }
);


// =====================================================
// LOAD USER SUMMARY
// =====================================================

function loadUserSummary() {

    fetch("/api/user/summary")

        .then(function (response) {

            if (!response.ok) {

                throw new Error(
                    "Unable to load summary."
                );

            }

            return response.json();

        })

        .then(function (data) {

            if (data.error) {

                console.error(data.error);

                return;
            }


            document.getElementById(
                "currentDemand"
            ).textContent =
                Number(data.current).toFixed(2);


            document.getElementById(
                "averageDemand"
            ).textContent =
                Number(data.average).toFixed(2);


            document.getElementById(
                "maximumDemand"
            ).textContent =
                Number(data.maximum).toFixed(2);

        })

        .catch(function (error) {

            console.error(
                "Summary error:",
                error
            );


            document.getElementById(
                "currentDemand"
            ).textContent = "N/A";


            document.getElementById(
                "averageDemand"
            ).textContent = "N/A";


            document.getElementById(
                "maximumDemand"
            ).textContent = "N/A";

        });

}


// =====================================================
// LOAD ELECTRICITY DEMAND CHART
// =====================================================

function loadDemandChart() {

    fetch("/api/user/consumption")

        .then(function (response) {

            if (!response.ok) {

                throw new Error(
                    "Unable to load consumption data."
                );

            }

            return response.json();

        })

        .then(function (data) {

            if (data.error) {

                console.error(data.error);

                return;
            }


            const canvas =
                document.getElementById(
                    "demandChart"
                );


            if (!canvas) {

                console.error(
                    "demandChart canvas not found."
                );

                return;
            }


            const ctx =
                canvas.getContext("2d");


            new Chart(
                ctx,
                {

                    type: "line",

                    data: {

                        labels: data.labels,

                        datasets: [

                            {

                                label:
                                    "Electricity Demand",

                                data:
                                    data.values,

                                borderWidth: 3,

                                tension: 0.35,

                                fill: true,

                                pointRadius: 3,

                                pointHoverRadius: 6

                            }

                        ]

                    },


                    options: {

                        responsive: true,

                        maintainAspectRatio: false,

                        interaction: {

                            intersect: false,

                            mode: "index"

                        },


                        plugins: {

                            legend: {

                                display: true

                            }

                        },


                        scales: {

                            x: {

                                ticks: {

                                    maxRotation: 45,

                                    minRotation: 0

                                }

                            },


                            y: {

                                beginAtZero: false,

                                title: {

                                    display: true,

                                    text:
                                        "Electricity Demand"

                                }

                            }

                        }

                    }

                }
            );

        })


        .catch(function (error) {

            console.error(
                "Chart error:",
                error
            );

        });

}