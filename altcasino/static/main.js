document.documentElement.style.overflowX = "hidden";

var animation = anime({
  targets: "div.coin",
  translateY: [{ value: -300, duration: 1200 }, { value: 0, duration: 800 }],
  delay: 500,
  width: {
    value: "1px", // 28 - 20 = '8px'
    duration: 1800,
    easing: "easeInOutSine"
  },
  rotate: {
    value: "+=4turn", // 0 + 2 = '2turn'
    duration: 1800,
    easing: "easeInOutSine"
  },
  width: {
    value: "100px", // 28 - 20 = '8px'
    duration: 1800,
    easing: "easeInOutSine"
  },
  loop: false,
  autoplay: false
});

document.querySelector(".heads").onclick = animation.restart;
document.querySelector(".tails").onclick = animation.restart;

var rollboth = function rollboth() {
  anime({
    targets: "div.dice1",
    translateX: Math.floor(Math.random() * 400) + 10,
    translateY: Math.floor(Math.random() * 100) + 10,
    scale: 1.2,
    rotate: function() {
      return anime.random(0, 360);
    }
  });

  anime({
    targets: "div.dice2",
    translateX: Math.floor(Math.random() * 200) + 10,
    translateY: Math.floor(Math.random() * 200) + 10,
    scale: 1.2,
    rotate: function() {
      return anime.random(0, 360);
    }
  });
  return;
};
$("#roll").on("click", function(e) {
  e.preventDefault();
  rollboth();
});

// document.querySelector(".roll").onclick = rolldice2.restart;
// Begin Jquery
$("#half").on("click", function(e) {
  e.preventDefault();
  half = $("#bet").val() / 2;
  $("#bet").val(half);
});

$("#time2").on("click", function(e) {
  e.preventDefault();
  time2 = $("#bet").val() * 2;
  $("#bet").val(time2);
  var bet = $("#bet").val();
  console.log(bet);
  var max = 150;
  if (bet > max) {
    let bet = $("#bet").val("150");
  }
  return bet;
});

$("#max").on("click", function(e) {
  e.preventDefault();
  $("#bet").val("150");
  console.log(bet);
  return bet;
});
function reset() {
  $("#placeResult").show();
  $("#coin").css("background-color", "#f5a623");
}
function showResultT() {
  $("#placeResult").show();
  // var showCoin = document.getElementById("placeResult");
  $("#coin").css("background-color", "white");
  // showCoin.innerHTML = "";
}
function showResultH() {
  $("#placeResult").show();
  var showCoin = document.getElementById("placeResult");
  showCoin.innerHTML = "";
}
// For Heads
$(document).ready(function() {
  $("#heads").on("click", function(e) {
    $("#placeResult").hide();
    reset();
    $.ajax({
      data: {
        bet: $("#bet").val(),
        heads: $("#heads").val(),
        tails: $("#tails").val(),
        choice: "Heads"
      },
      type: "POST",
      url: "/process"
    }).done(function(data) {
      $("#heads").hide();
      $("#tails").hide();
      if (data.error) {
        $("#errorAlert")
          .delay(1500)
          .text(data.error)
          .delay("slow")
          .fadeIn()
          .delay("slow")
          .fadeOut();
        $("#placeResult").hide();
        setTimeout(showResultT, 1500);
        $("#successAlert").hide();
      } else if (data.nobalance) {
        $("#errorAlert")
          .text(data.nobalance)
          .delay("slow")
          .fadeIn()
          .delay("slow")
          .fadeOut();
        $("#successAlert").hide();
      } else if (data.result) {
        $("#successAlert")
          .delay(1500)
          .text(data.result)
          .delay("slow")
          .fadeIn()
          .delay("slow")
          .fadeOut();
        $("#placeResult").hide();
        setTimeout(showResultH, 1500);
        $("#errorAlert").hide();
      }
      if (data.increase) {
        $("#userbalance")
          .delay(1000)
          .fadeIn()
          .text(data.increase);
      } else if (data.decrease) {
        $("#userbalance")
          .delay(1000)
          .fadeIn()
          .text(data.decrease);
      }
      $("#heads")
        .delay(1500)
        .fadeIn("slow");
      $("#tails")
        .delay(1500)
        .fadeIn("slow");
      setTimeout(function getbal() {
        $.get("/processget", function(data) {
          $("#userbalance").text("BALANCE: " + data.increase);
        });
      }, 2000);
    });

    e.preventDefault();
  });
});

// For Tails
$(document).ready(function() {
  $("#tails").on("click", function(e) {
    $("#placeResult").hide();
    reset();
    $.ajax({
      data: {
        bet: $("#bet").val(),
        heads: $("#heads").val(),
        tails: $("#tails").val(),
        choice: "Tails"
      },
      type: "POST",
      url: "/process"
    }).done(function(data) {
      $("#heads").hide();
      $("#tails").hide();
      if (data.error) {
        $("#errorAlert")
          .delay(1500)
          .text(data.error)
          .delay("slow")
          .fadeIn()
          .delay("slow")
          .fadeOut();
        $("#placeResult").hide();
        setTimeout(showResultH, 1500);
        $("#successAlert").hide();
      } else if (data.nobalance) {
        $("#errorAlert")
          .text(data.nobalance)
          .delay("slow")
          .fadeIn()
          .delay("slow")
          .fadeOut();
        $("#successAlert").hide();
      } else if (data.result) {
        $("#successAlert")
          .delay(1500)
          .text(data.result)
          .delay("slow")
          .fadeIn()
          .delay("slow")
          .fadeOut();
        $("#placeResult").hide();
        setTimeout(showResultT, 1500);
        $("#errorAlert").hide();
      }
      if (data.increase) {
        $("#userbalance")
          .delay(1000)
          .text(data.increase);
      } else if (data.decrease) {
        $("#userbalance")
          .delay(1000)
          .text(data.decrease);
      }
      $("#heads")
        .delay(1500)
        .fadeIn("slow");
      $("#tails")
        .delay(1500)
        .fadeIn("slow");
      setTimeout(function getbal() {
        $.get("/processget", function(data) {
          $("#userbalance").text("BALANCE: " + data.increase);
        });
      }, 2000);
    });

    e.preventDefault();
  });
});

var util = {
  mobileMenu() {
    $("#nav").toggleClass("nav-visible");
  },
  windowResize() {
    if ($(window).width() > 800) {
      $("#nav").removeClass("nav-visible");
    }
  },
  scrollEvent() {
    var scrollPosition = $(document).scrollTop();

    $.each(util.scrollMenuIds, function(i) {
      var link = util.scrollMenuIds[i],
        container = $(link).attr("href"),
        containerOffset = $(container).offset().top,
        containerHeight = $(container).outerHeight(),
        containerBottom = containerOffset + containerHeight;

      if (
        scrollPosition < containerBottom - 20 &&
        scrollPosition >= containerOffset - 20
      ) {
        $(link).addClass("active");
      } else {
        $(link).removeClass("active");
      }
    });
  }
};
