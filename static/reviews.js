// Get reference to template
var scroller = document.querySelector('#scroller');
var no_comments = document.querySelector('#no-reviews');
var template = document.querySelector('#comment_template');


// Get current open book id from session
var curr_link = window.location.href
var curr_link_array  = curr_link.split("/");
var book_id = parseInt(curr_link_array[curr_link_array.length - 1])

console.log("Open link: " + book_id);
// Function to load all comments
function loadComments() {
    // Use fetch to load all the comments
    fetch(`/load_reviews?book_id=${book_id}`).then((response) => {
        // Convert the response data to JSON
        response.json().then((data) => {
            console.log("Got data")
            // If empty JSON, exit the function
            if (!data.length) {
                // Display no comments somewhere
                no_comments.value = "No Reviews Yet"
                return
            }

            // Iterate over the items in the response
            for (var i = 0; i < data.length; i++){

                // Clone the comments template
                let template_clone = template.content.cloneNode(true);

                // Query & update the template content
                template_clone.querySelector("#review").innerHTML = `${data[i][0]}`;
                template_clone.querySelector("#username").innerHTML =  data[i][1];

                // Append template to dom
                scroller.appendChild(template_clone);
            }
        })

    })

}
loadComments();