import Button from 'react-bootstrap/Button'

const RiskButton = (props) => {
  
  const variant = props.status === 'pass' ? 'success' :
   props.status === 'warning' ? 'warning' : 
   props.status === 'fail' ? 'danger' : 'secondary'
  
   return (
    <Button variant={variant}>{props.status}</Button>
  )
}

export default RiskButton