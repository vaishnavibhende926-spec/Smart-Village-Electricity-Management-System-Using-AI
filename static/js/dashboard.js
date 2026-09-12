document.addEventListener("DOMContentLoaded", function () {

```
console.log(
    "Smart Village Electricity Dashboard Loaded"
);


const canvas =
    document.getElementById("demandChart");


if (!canvas) {

    console.log(
        "Demand chart element not found."
    );

    return;
}


/*
 * Get REAL electricity demand data
 * from the Flask API.
 */

fetch("/api/demand")

    .then(function (response) {

        return response.json();

    })

    .then(function (data) {

        console.log(
            "Real demand data received:",
            data
        );


        if (
            !data.labels ||
            data.labels.length === 0
        ) {

            console.log(
                "No electricity demand data available."
            );

            return;
        }


        const ctx =
            canvas.getContext("2d");


        new Chart(ctx, {

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


                        fill: true,


                        tension: 0.4,


                        pointRadius: 3

                    }

                ]

            },


            options: {

                responsive: true,


                maintainAspectRatio: false,


                plugins: {

                    legend: {

                        display: true

                    }

                },


                scales: {

                    y: {

                        beginAtZero: false,


                        title: {

                            display: true,

                            text:
                                "Electricity Demand"

                        }

                    },


                    x: {

                        title: {

                            display: true,

                            text:
                                "Date & Time"

                        }

                    }

                }

            }

        });

    })


    .catch(function (error) {

        console.error(
            "Error loading demand data:",
            error
        );

    });
```

});
