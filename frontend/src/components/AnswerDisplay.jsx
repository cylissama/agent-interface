const AnswerDisplay = ({ answer }) => {
  if (!answer) {
    return null;
  }

  return (
    <section>
      <h2>Assistant Response</h2>
      <p>{answer}</p>
    </section>
  );
};

export default AnswerDisplay;
