import React from "react"

const Cusupdate = () => {

  const handleSubmit = async () => {
    // FormData 생성 및 데이터 추가
 
    axios.post('http://192.168.0.66:8001/update_qs', 
      {user_id: "ygang4546@gmail.com",
        itv_no: "1",
        qs_no: job,
        qs_content: "자소서",
        qs_video_url: "",
        qs_audio_url: "",
        qs_text_url: ""
      })
    .then(function (response) {
      console.log(response);
    })
    .catch(function (error) {
      console.log(error);
    });

    // router.push('/information');
  };


  return (
    <div>UpdateQ Page</div>
  );
};
export default Cusupdate;