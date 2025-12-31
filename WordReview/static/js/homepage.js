// Get Quote of the Day from Wikiquote
$.ajax({
  url: "https://en.wikiquote.org/w/api.php?format=json&action=parse&prop=text&page=Main%20Page",
  dataType: "jsonp",
  timeout: 5000 // Set timeout to 5 seconds
}).done(function (response) {
  let $qotd = $("#tmpl-qotd");
  let minH = 100;
  
  // Check if response contains the expected data
  if (response && response.parse && response.parse.text && response.parse.text["*"]) {
    $qotd.html(response.parse.text["*"]);
    
    // Find the daily quote element
    let $mfQotd = $("#mf-qotd");
    if ($mfQotd.length > 0) {
      $qotd.html(
        $mfQotd.html().replace(/href="\//g, 'href="https://en.wikiquote.org/')
      );

      // Delete unnecessary nodes
      $qotd.find("small").empty();
      let divs = $qotd.find("div").find("div");
      if (divs.length > 0) {
        divs[0].innerHTML = "";
      }

      // Adjust alignment
      let tdElements = $qotd.find("td");
      if (tdElements.length > 0) {
        let nestedTds = tdElements.find("td");
        if (nestedTds.length > 2) {
          let trElements = nestedTds.eq(2).find("tr");
          if (trElements.length > 0) {
            trElements.eq(0).css("text-align", "left");
          }
        }
      }

      // Adjust image
      let $img = $qotd.find("img");
      if ($img.length > 0) {
        $img.css("margin-left", "5px");
        let w = $img.width() || 100;
        let h = $img.height() || 100;
        $img.height(minH);
        $img.width((minH / h) * w);

        let H = $qotd.height();
        if (H > minH) {
          $img.height(H);
          $img.width((H / h) * w);
        }
      }
    } else {
      // If #mf-qotd not found, show error message
      $qotd.html("<p style='color: #666; font-style: italic;'>每日名言获取失败：未找到名言元素</p>");
    }
  } else {
    // If response format is incorrect, show error message
    $qotd.html("<p style='color: #666; font-style: italic;'>每日名言获取失败：响应格式错误</p>");
  }
}).fail(function (jqXHR, textStatus, errorThrown) {
  // Handle AJAX request failure
  let $qotd = $("#tmpl-qotd");
  let errorMsg = "每日名言获取失败：";
  
  if (textStatus === "timeout") {
    errorMsg += "请求超时，请检查网络连接";
  } else if (textStatus === "error") {
    errorMsg += "网络错误";
  } else if (textStatus === "parsererror") {
    errorMsg += "解析错误";
  } else {
    errorMsg += "未知错误：" + textStatus;
  }
  
  $qotd.html("<p style='color: #666; font-style: italic;'>" + errorMsg + "</p>");
  console.error("QOTD AJAX Error:", textStatus, errorThrown);
});

$.ajax({
  url: "https://api.github.com/repos/Benature/WordReview/commits",
}).done(function (response) {
  let latest = response[0].commit;
  let date = latest.committer.date.replace("T", " ").replace("Z", "");
  $("#github-commit").text(
    "上一次源码更新于" + date + "，更新附言为「" + latest.message + "」"
  );
});

$(function () {
  $(".list-block").on("click", function (e) {
    document.location.href = $(this).attr("href");
  });
});

$(document).keyup(function (e) {
  // console.log(e.keyCode);
  if (89 == e.keyCode) {
    $("#yesterday-mode").click();
  } else if (67 == e.keyCode) {
    document.location = "/calendar/";
  }
});
