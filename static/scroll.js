// Get references to the dom elements
var scroller = document.querySelector("#scroller");
var template = document.querySelector('#post_template');
var sentinel = document.querySelector('#sentinel');
var alert = document.querySelector('#alert');
alert.style.display = "none";
var book_id = 0;
// Set a counter to count the items loaded
var counter = 0;


// Function to request new items and render to the dom
function loadItems() {

  // Use fetch to request data and pass the counter value in the QS
  fetch(`/load?c=${counter}`).then((response) => {

    // Convert the response data to JSON
    response.json().then((data) => {

      // If empty JSON, exit the function
      if (!data.length) {

        // Replace the spinner with "No more posts"
        sentinel.innerHTML = "No more posts";
        return;
      }

      // Iterate over the items in the response
      for (var i = 0; i < data.length; i++) {

        // Clone the HTML template
        let template_clone = template.content.cloneNode(true);

        // Query & update the template content
        template_clone.querySelector("#book").innerHTML = `${data[i][0]}`;
        template_clone.querySelector("#author").innerHTML = "Author: " + data[i][2];
        template_clone.querySelector("#isbn").innerHTML = "ISBN#: " + data[i][1];
        template_clone.getElementById("book-link").href = "/profile/" + data[i][3].toString();
        template_clone.getElementById("add-btn").name = data[i][3].toString();
        // Append template to dom
        scroller.appendChild(template_clone);

        // Increment the counter
        counter += 1;
      }
    })
  })
}

// Create a new IntersectionObserver instance
var intersectionObserver = new IntersectionObserver(entries => {

  // Uncomment below to see the entry.intersectionRatio when
  // the sentinel comes into view

  // entries.forEach(entry => {
  //   console.log(entry.intersectionRatio);
  // })

  // If intersectionRatio is 0, the sentinel is out of view
  // and we don't need to do anything. Exit the function
  if (entries[0].intersectionRatio <= 0) {
    return;
  }

  // Call the loadItems function
  loadItems();

});

// Instruct the IntersectionObserver to watch the sentinel
intersectionObserver.observe(sentinel);

function own_book(clicked_id)
{
    var book_id = clicked_id.name;
    clicked_id.disabled = true;
      // Use fetch to request data and pass the counter value in the QS
  fetch(`/own_book?book_id=${book_id}`).then((response) => {

    // Convert the response data to JSON
    response.json().then((data) => {
      // Create a notification telling the user that they added the book
      alert.style.display = "inline";
    })
  })
}
